from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.langgraph_workflow import TriageOrchestrator
from src.fraud_detection.telemetry import compute_kpis

router = APIRouter(tags=["banking"])


class TransactionInput(BaseModel):
	account_id: str
	amount: float
	currency: str | None = "USD"
	merchant: str | None = None
	mcc: str | None = None
	geo: str | None = None
	device_id: str | None = None
	channel: str | None = None
	timestamp: str | None = None


class ApplicationInput(BaseModel):
	applicant_id: str
	income: float
	liabilities: float
	delinquency_flags: list[str] | None = []
	requested_limit: float | None = None
	# New fields for ML model
	credit_utilization: float | None = None  # 0-100 percentage
	credit_history_months: int | None = None  # Length of credit history
	employment_months: int | None = None  # Time at current job
	age: int | None = None  # Applicant age
	current_balance: float | None = None  # Current credit balance
	credit_limit: float | None = None  # Current credit limit
	loan_type: str = "bnpl"  # credit_card, bnpl, personal_loan


# ========================================
# FRAUD TRIAGE ENDPOINTS
# ========================================

@router.post("/fraud/triage")
async def fraud_triage(input_txn: TransactionInput):
	"""
	Fraud Triage with Novel Features:
	- Risk Factor Breakdown (Explainable AI)
	- Anomaly Score Analysis
	- Recommended Actions
	"""
	agent = FraudTriageAgent()
	result = agent.triage(
		amount=input_txn.amount,
		mcc=input_txn.mcc,
		geo=input_txn.geo,
		device_id=input_txn.device_id,
		history=[],
		now=datetime.utcnow(),
	)

	# Build summary
	risk_score = round(float(result.alert_score) * 100)
	risk_band = result.risk_band
	risk_label = risk_band.capitalize()
	decision_human = "Manual review recommended" if risk_band in {"medium", "high"} else "Approve"
	summary = f"{risk_label} Risk ({risk_score}/100): {decision_human}."

	# Record telemetry
	event_id = str(uuid4())
	tele = TriageEvent(
		event_id=event_id,
		timestamp_s=datetime.utcnow().timestamp(),
		intent="fraud",
		payload=input_txn.model_dump(),
		decision=str(result.decision),
		risk_band=str(result.risk_band),
		alert_score=float(result.alert_score),
		explanations=result.rule_hits,
		features=result.features,
		sla_ms=None,
	)
	record_event(tele)

	return {
		"event_id": event_id,
		"alert_score": result.alert_score,
		"decision": result.decision,
		"rationale": result.rationale,
		"policy_citations": result.policy_citations,
		"features": result.features,
		"risk_band": result.risk_band,
		"rule_hits": result.rule_hits,
		"summary": summary,
		# Novel fields
		"risk_factors": result.risk_factors,
		"anomaly_breakdown": result.anomaly_breakdown,
		"recommended_actions": result.recommended_actions,
	}


# ========================================
# CREDIT TRIAGE ENDPOINTS
# ========================================

@router.post("/credit/triage")
async def credit_triage(input_app: ApplicationInput):
	"""
	Credit Risk Triage with Fuzzy Logic + ML Fusion:
	
	Architecture:
	1. Fuzzy Logic Engine (10 rules based on RBI/Basel III/OCC)
	2. BrownBoost ML Model (pattern-based default prediction)
	3. Risk Fusion Engine (weighted combination)
	4. LLM Documentation (Gemini 2.5 Flash)
	
	Features:
	- Factor Contribution Analysis (SHAP-like)
	- What-If Scenario Simulator
	- AI-Powered Improvement Recommendations
	- Policy Violation Tracking
	"""
	from src.credit_risk.risk_fusion_engine import fuse_credit_risk
	from src.credit_risk.scorecard import simulate_what_if
	from src.core.config import get_settings
	
	# ==========================================
	# STEP 1: RUN CREDIT RISK AGENT (FUZZY + ML)
	# ==========================================
	agent = CreditRiskAgent()
	res = agent.triage(
		income=input_app.income,
		liabilities=input_app.liabilities,
		requested_limit=input_app.requested_limit,
		delinquency_flags=input_app.delinquency_flags,
		credit_utilization=input_app.credit_utilization,
		employment_months=input_app.employment_months,
		credit_history_months=input_app.credit_history_months,
		age=input_app.age,
		loan_type=input_app.loan_type,
	)
	
	# Mapping result to response format
	fusion_result = res
	
	# Calculate DTI for display
	dti = round((input_app.liabilities / input_app.income * 100), 1) if input_app.income > 0 else 0
	
	# Calculate suggested limit (conservative: 25% of income)
	limit_suggested = round(input_app.income * 0.25, 2)
	
	# ==========================================
	# STEP 2: GENERATE WHAT-IF SCENARIOS
	# ==========================================
	what_if_scenarios = []
	delinquencies = len(input_app.delinquency_flags or [])
	
	if input_app.liabilities > 0:
		debt_reduction_20 = round(input_app.liabilities * 0.2, 2)
		scenario1 = simulate_what_if(
			current_income=input_app.income,
			current_liabilities=input_app.liabilities,
			current_delinquencies=delinquencies,
			requested_limit=input_app.requested_limit,
			liability_reduction=debt_reduction_20,
			delinquency_flags=input_app.delinquency_flags,
		)
		what_if_scenarios.append({
			"name": "Pay off 20% of debt",
			"action": f"Reduce liabilities by ${debt_reduction_20:,.2f}",
			**scenario1
		})
	
	# ==========================================
	# STEP 3: GENERATE LLM RATIONALE
	# ==========================================
	settings = get_settings()
	rationale = ""
	
	if settings.google_api_key and settings.google_api_key not in ["your_google_api_key_here", ""]:
		try:
			import google.generativeai as genai
			genai.configure(api_key=settings.google_api_key)
			model = genai.GenerativeModel('gemini-2.5-flash')
			
			prompt = f"""You are a Senior Credit Underwriter. Write a professional rationale for this credit decision.

=== FUSION ANALYSIS RESULTS ===
Decision: {fusion_result.decision.upper()}
Final Score: {fusion_result.final_score}/100 (Confidence: {fusion_result.confidence:.0%})

Fuzzy Logic Score: {fusion_result.fuzzy_score}/100 ({fusion_result.fuzzy_band})
ML Default Probability: {fusion_result.ml_probability:.1%} ({fusion_result.ml_risk_level} Risk)
Fused Risk Level: {fusion_result.fused_risk_level}

=== KEY FACTORS ===
{chr(10).join(fusion_result.combined_factors)}

=== POLICY VIOLATIONS ===
{chr(10).join(fusion_result.policy_violations) if fusion_result.policy_violations else 'None detected'}

=== HARD DECLINE ===
{fusion_result.hard_decline_reason if fusion_result.hard_decline else 'Not applicable'}

Write a 3-4 sentence professional rationale that:
1. States the decision clearly
2. References both Fuzzy Logic and ML model findings
3. Cites specific policy violations if any
4. Suggests one improvement action if decision is not approve

Respond with ONLY the rationale text. Be professional."""

			response = model.generate_content(prompt)
			rationale = response.text.strip()
		except Exception as e:
			rationale = f"Decision: {fusion_result.decision.upper()}. Score: {fusion_result.final_score}/100. Risk Level: {fusion_result.fused_risk_level}."
	else:
		rationale = f"Decision: {fusion_result.decision.upper()}. Combined Fuzzy ({fusion_result.fuzzy_score:.0f}) + ML ({fusion_result.ml_score:.0f}) = {fusion_result.final_score:.0f}/100. Risk: {fusion_result.fused_risk_level}."
	
	# ==========================================
	# STEP 4: BUILD RESPONSE
	# ==========================================
	return {
		# Core decision
		"score": res.score,
		"decision": res.decision,
		"rationale": res.rationale,
		"dti": f"{dti}%",
		"limit_suggested": limit_suggested,
		
		# Explanations
		"key_factors": res.key_factors,
		"policy_citations": res.policy_citations,
		
		# Novel fields
		"factor_breakdown": res.factor_breakdown,
		"improvement_tips": res.improvement_tips,
		"what_if_scenarios": res.what_if_scenarios,
		"risk_summary": res.risk_summary,
		
		# Detailed logic outputs
		"fuzzy_score": res.fuzzy_score,
		"fuzzy_rules": res.fuzzy_rules_fired,
		"fuzzy_dominant_rules": res.fuzzy_dominant_rules,
		"policy_violations": res.policy_violations,
		"hard_decline": res.hard_decline,
		"hard_decline_reason": res.hard_decline_reason,
	}


# ========================================
# ANALYTICS ENDPOINTS
# ========================================

@router.get("/analytics/kpis")
async def analytics_kpis():
	return compute_kpis()


class LabelBody(BaseModel):
	event_id: str
	label: str  # 'fraud' | 'genuine'


@router.post("/fraud/label")
async def fraud_label(body: LabelBody):
	return record_label(body.event_id, body.label)


@router.get("/fraud/events")
async def fraud_events(limit: int | None = 50):
	items = []
	for e in iter_events(limit=limit or None):
		items.append({
			"event_id": e.event_id,
			"timestamp_s": e.timestamp_s,
			"intent": e.intent,
			"decision": e.decision,
			"risk_band": e.risk_band,
			"alert_score": e.alert_score,
			"explanations": e.explanations,
			"sla_ms": e.sla_ms,
			"features": e.features,
		})
	return {"items": items}


# ========================================
# RULE MANAGEMENT ENDPOINTS
# ========================================

class RuleSuggestionRequest(BaseModel):
	limit: int | None = 3


@router.post("/fraud/rules/suggest")
async def fraud_rules_suggest(body: RuleSuggestionRequest):
	items = list(iter_events(limit=None))
	def estimate(condition_fn):
		count = 0
		for e in items:
			try:
				if condition_fn(e.features):
					count += 1
			except Exception:
				pass
		return count

	suggestions = []
	cond_velocity = lambda f: float(f.get("velocity_1h_count", 0.0)) >= 5.0
	cond_mcc = lambda f: float(f.get("high_risk_mcc", 0.0)) >= 1.0
	cond_night = lambda f: float(f.get("is_night", 0.0)) >= 1.0

	for key, desc, weight, cond in [
		("velocity_1h_count", "High velocity in last 1h", 0.2, cond_velocity),
		("high_risk_mcc", "High-risk MCC", 0.2, cond_mcc),
		("is_night", "Night-time transaction", 0.05, cond_night),
	]:
		count = estimate(cond)
		suggestions.append({
			"rule_id": f"suggest-{key}",
			"description": desc,
			"proposed_weight": weight,
			"condition": {"feature": key, "operator": ">=", "value": 1 if key != "velocity_1h_count" else 5},
			"support": count,
		})

	return {"suggestions": suggestions[: max(0, int(body.limit or 3))]}


class RuleAcceptBody(BaseModel):
	description: str
	feature: str
	operator: str = ">="
	value: float = 1.0
	weight: float = 0.05


@router.get("/fraud/rules/runtime")
async def get_rules_runtime():
	return {"rules": get_runtime_rules()}


@router.post("/fraud/rules/runtime")
async def post_rules_runtime(body: RuleAcceptBody):
	return {"accepted": add_runtime_rule(body.model_dump())}


@router.delete("/fraud/rules/runtime")
async def delete_rules_runtime():
	clear_runtime_rules()
	return {"status": "cleared"}


# ========================================
# FRAUD CONFIG ENDPOINTS
# ========================================

@router.get("/fraud/config")
async def get_fraud_config():
	cfg = get_config()
	return {
		"fraud_types": cfg.fraud_types,
		"anomaly_method": cfg.anomaly_method,
		"thresholds": {
			"medium_band_threshold": cfg.thresholds.medium_band_threshold,
			"high_band_threshold": cfg.thresholds.high_band_threshold,
		},
		"cost_matrix": {
			"true_positive_savings": cfg.cost_matrix.true_positive_savings,
			"false_positive_cost": cfg.cost_matrix.false_positive_cost,
			"false_negative_cost": cfg.cost_matrix.false_negative_cost,
			"true_negative_savings": cfg.cost_matrix.true_negative_savings,
		},
	}


class UpdateFraudConfig(BaseModel):
	fraud_types: list[str] | None = None
	anomaly_method: str | None = None
	thresholds: dict | None = None
	cost_matrix: dict | None = None


@router.put("/fraud/config")
async def put_fraud_config(body: UpdateFraudConfig):
	return update_config(**{k: v for k, v in body.model_dump().items() if v is not None})


# ========================================
# ML MODEL ENDPOINTS
# ========================================

@router.post("/fraud/train-iforest")
async def train_iforest():
	rows = []
	for i in range(200):
		rows.append({
			"velocity_1h_count": 0.0,
			"velocity_1h_total": 0.0,
			"velocity_24h_count": float(i % 5),
			"velocity_24h_total": float((i % 7) * 20),
			"amount_zscore": float((i % 10) / 10.0),
			"device_novelty": 0.0,
			"geo_novelty": 0.0,
			"high_risk_mcc": 1.0 if (i % 30 == 0) else 0.0,
			"hour_of_day": float(i % 24),
			"is_night": 1.0 if (i % 24 < 6 or i % 24 >= 22) else 0.0,
			"first_time_mcc": 0.0,
		})
	info = train_from_feature_rows(rows)
	return {"status": "ok", "model": {"loaded": info.loaded, "n_features": info.n_features, "feature_names": info.feature_names}}


@router.get("/fraud/model-info")
async def fraud_model_info():
	info = get_model_info()
	return {"loaded": info.loaded, "n_features": info.n_features, "feature_names": info.feature_names}


# ========================================
# UNIFIED TRIAGE (ORCHESTRATOR)
# ========================================

class TriageInput(BaseModel):
	payload: dict


@router.post("/triage")
async def unified_triage(body: TriageInput):
	orchestrator = TriageOrchestrator()
	result = orchestrator.invoke(body.payload)
	return result
