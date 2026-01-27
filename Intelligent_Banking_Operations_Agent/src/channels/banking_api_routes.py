from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

from src.agents.fraud_triage_agent import FraudTriageAgent
from src.fraud_detection.feature_engineering import HistoricalTxn
from src.fraud_detection.fraud_config import get_config, update_config
from src.fraud_detection.iforest_model import train_from_feature_rows, get_model_info
from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.langgraph_workflow import TriageOrchestrator
from src.fraud_detection.telemetry import record_event, record_label, compute_kpis, TriageEvent, iter_events
from src.fraud_detection.rules_runtime import get_runtime_rules, add_runtime_rule, clear_runtime_rules

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


@router.post("/fraud/triage")
async def fraud_triage(input_txn: TransactionInput):
	# For demo: use empty history and run the agent
	agent = FraudTriageAgent()
	result = agent.triage(
		amount=input_txn.amount,
		mcc=input_txn.mcc,
		geo=input_txn.geo,
		device_id=input_txn.device_id,
		history=[],
		now=datetime.utcnow(),
	)

	# Build human-friendly explanations and summary
	features = getattr(result, "features", {}) or {}
	explanations: list[str] = []
	# if features.get("amount_zscore", 0.0) >= 3.5:
	# 	explanations.append(f"Transaction amount is {features['amount_zscore']:.1f}σ above the account's average")
	# if features.get("geo_novelty", 0.0) >= 1.0:
	# 	explanations.append("Transaction originates from a new or high-risk geographical location")
	# if features.get("device_novelty", 0.0) >= 1.0:
	# 	explanations.append("Device ID has not been seen on this account before")
	# if features.get("high_risk_mcc", 0.0) >= 1.0 and input_txn.mcc:
	# 	explanations.append(f"Merchant Category ({input_txn.mcc}) is flagged as high-risk")
	# if features.get("velocity_1h_count", 0.0) >= 5:
	# 	explanations.append("High transaction velocity in the last 1 hour")

	# Always include rule hits (if any) to preserve transparency
	# for hit in getattr(result, "rule_hits", []) or []:
	# 	if hit not in explanations:
	# 		explanations.append(hit)

	risk_score = round(float(getattr(result, "alert_score", 0.0)) * 100)
	risk_band = getattr(result, "risk_band", "low")
	risk_label = risk_band.capitalize()
	decision_human = "Manual review recommended" if risk_band in {"medium", "high"} else "Approve"
	summary = f"{risk_label} Risk ({risk_score}/100): {decision_human}."

	# Minimal event_id and telemetry record
	event_id = str(uuid4())
	tele = TriageEvent(
		event_id=event_id,
		timestamp_s=datetime.utcnow().timestamp(),
		intent="fraud",
		payload=input_txn.model_dump(),
		decision=str(result.decision),
		risk_band=str(result.risk_band),
		alert_score=float(result.alert_score),
		explanations=list(explanations),
		features=features,
		sla_ms=None,
	)
	record_event(tele)

	# SLA measurement (ms)
	# Note: For this demo path, we don't capture monotonic start/end in handler; reuse fraud agent fast path
	sla_ms = None
	return {
		"event_id": event_id,
		"alert_score": result.alert_score,
		"decision": result.decision,
		"rationale": result.rationale,
		"policy_citations": result.policy_citations,
		"features": features,
		"risk_band": result.risk_band,
		"explanations": explanations,
		"summary": summary,
		"sla_ms": sla_ms,
	}


@router.post("/credit/triage")
async def credit_triage(input_app: ApplicationInput):
	agent = CreditRiskAgent()
	res = agent.triage(
		income=input_app.income,
		liabilities=input_app.liabilities,
		delinquency_flags=input_app.delinquency_flags,
		requested_limit=input_app.requested_limit,
	)
	return {
		"score": res.score,
		"decision": res.decision,
		"rationale": res.rationale,
		"policy_citations": res.policy_citations,
		"key_factors": res.key_factors,
	}


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


class RuleSuggestionRequest(BaseModel):
	limit: int | None = 3


@router.post("/fraud/rules/suggest")
async def fraud_rules_suggest(body: RuleSuggestionRequest):
	# Very simple heuristic suggestions from telemetry
	# 1) velocity_1h_count >= 5
	# 2) high_risk_mcc == 1
	# 3) is_night == 1
	items = list(iter_events(limit=None))
	def estimate(condition_fn):
		# naive estimates vs labels embedded in explanations not available; use counts only
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


@router.post("/fraud/train-iforest")
async def train_iforest():
	# In a real system, pull historical feature rows from a feature store
	# Here we synthesize a few rows using simple distributions
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


class TriageInput(BaseModel):
	payload: dict


@router.post("/triage")
async def unified_triage(body: TriageInput):
	orchestrator = TriageOrchestrator()
	result = orchestrator.invoke(body.payload)
	return result


