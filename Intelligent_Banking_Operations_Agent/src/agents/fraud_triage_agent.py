from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from time import perf_counter

from src.fraud_detection.feature_engineering import HistoricalTxn, build_features
from src.fraud_detection.rule_engine import evaluate_rules
from src.fraud_detection.anomaly_detector import choose_anomaly_score
from src.fraud_detection.fraud_config import get_config


@dataclass
class FraudTriageOutput:
	alert_score: float
	decision: str
	rationale: str
	policy_citations: list[str]
	features: dict[str, Any]
	risk_band: str
	rule_hits: list[str]
	# Novel fields for enhanced analysis
	risk_factors: list[dict] = field(default_factory=list)
	anomaly_breakdown: dict = field(default_factory=dict)
	recommended_actions: list[str] = field(default_factory=list)


class FraudTriageAgent:
	"""
	Enhanced Fraud Triage Agent with Novel Features:
	1. Risk Factor Breakdown (Explainable AI - like SHAP)
	2. Anomaly Score Component Analysis
	3. Recommended Actions based on risk level
	
	ARCHITECTURE (per CFA Institute RAG Research):
	- ALL calculations done by Python (rule scores, anomaly scores, etc.)
	- LLM only receives pre-calculated values and writes explanatory text
	- LLM NEVER performs calculations - prevents hallucination
	"""

	def triage(self, *, amount: float, mcc: str | None, geo: str | None, device_id: str | None, history: list[HistoricalTxn], now: datetime | None = None) -> FraudTriageOutput:
		now = now or datetime.utcnow()
		started = perf_counter()
		
		# ========================================
		# STEP 1: ALL CALCULATIONS DONE IN PYTHON
		# ========================================
		
		features = build_features(amount, now, mcc, geo, device_id, history)
		rule_score, rule_hits = evaluate_rules(features)

		cfg = get_config()
		anom = choose_anomaly_score(features, preferred_method=cfg.anomaly_method)
		anomaly_score = float(anom.score)
		
		# Weighted combination of rule-based and ML-based scores
		rule_weight = 0.6
		anomaly_weight = 0.4
		alert_score = max(0.0, min(1.0, rule_weight * rule_score + anomaly_weight * anomaly_score))

		# Determine decision band
		if alert_score >= cfg.thresholds.high_band_threshold:
			decision = "alert-high"
			risk_band = "high"
		elif alert_score >= cfg.thresholds.medium_band_threshold:
			decision = "alert-medium"
			risk_band = "medium"
		else:
			decision = "allow"
			risk_band = "low"

		reasons = ", ".join(rule_hits) if rule_hits else "no significant rule triggers"
		
		# === NOVEL FEATURE 1: Risk Factor Breakdown ===
		risk_factors = []
		
		# Amount Z-Score analysis
		amount_zscore = features.get("amount_zscore", 0.0)
		if amount_zscore >= 4.0:
			risk_factors.append({
				"factor": "Transaction Amount",
				"value": f"{amount_zscore:.1f}σ above average",
				"severity": "critical",
				"contribution": round(min(0.3, amount_zscore * 0.05) * 100),
				"description": f"Amount is {amount_zscore:.1f} standard deviations above typical transactions"
			})
		elif amount_zscore >= 2.5:
			risk_factors.append({
				"factor": "Transaction Amount",
				"value": f"{amount_zscore:.1f}σ above average",
				"severity": "high",
				"contribution": round(amount_zscore * 0.04 * 100),
				"description": f"Amount is unusually high ({amount_zscore:.1f}σ)"
			})
		
		# Velocity analysis
		velocity_1h = features.get("velocity_1h_count", 0)
		if velocity_1h >= 5:
			risk_factors.append({
				"factor": "Transaction Velocity",
				"value": f"{int(velocity_1h)} txns in 1 hour",
				"severity": "high",
				"contribution": 20,
				"description": f"High frequency: {int(velocity_1h)} transactions in the last hour"
			})
		
		# Device novelty
		if features.get("device_novelty", 0) >= 1.0:
			risk_factors.append({
				"factor": "Device Recognition",
				"value": "New device",
				"severity": "medium",
				"contribution": 15,
				"description": "Transaction from an unrecognized device"
			})
		
		# Geo novelty
		if features.get("geo_novelty", 0) >= 1.0:
			risk_factors.append({
				"factor": "Geographic Location",
				"value": "New location",
				"severity": "medium",
				"contribution": 15,
				"description": "Transaction from an unusual geographic location"
			})
		
		# High-risk MCC
		if features.get("high_risk_mcc", 0) >= 1.0:
			risk_factors.append({
				"factor": "Merchant Category",
				"value": f"MCC: {mcc}",
				"severity": "high",
				"contribution": 20,
				"description": f"Merchant category {mcc} is flagged as high-risk"
			})
		
		# Night-time transaction
		if features.get("is_night", 0) >= 1.0:
			risk_factors.append({
				"factor": "Transaction Time",
				"value": "Night hours (10PM-6AM)",
				"severity": "low",
				"contribution": 5,
				"description": "Transaction during unusual hours"
			})
		
		# === NOVEL FEATURE 2: Anomaly Breakdown ===
		anomaly_breakdown = {
			"method": anom.method if hasattr(anom, 'method') else cfg.anomaly_method,
			"raw_score": round(anomaly_score * 100),
			"rule_score": round(rule_score * 100),
			"weighted_final": round(alert_score * 100),
			"weights": {
				"rule_based": f"{int(rule_weight * 100)}%",
				"ml_anomaly": f"{int(anomaly_weight * 100)}%"
			},
			"interpretation": (
				"Strong anomaly detected" if anomaly_score >= 0.7 else
				"Moderate anomaly signals" if anomaly_score >= 0.4 else
				"Within normal patterns"
			)
		}
		
		# === NOVEL FEATURE 3: Recommended Actions ===
		recommended_actions = []
		
		if risk_band == "high":
			recommended_actions.append("BLOCK: Immediately decline and notify fraud team")
			recommended_actions.append("VERIFY: Contact customer through verified channel")
			recommended_actions.append("REVIEW: Examine last 24 hours of account activity")
		elif risk_band == "medium":
			recommended_actions.append("CHALLENGE: Request additional authentication (OTP/Biometric)")
			recommended_actions.append("MONITOR: Flag account for enhanced monitoring")
			recommended_actions.append("LOG: Record transaction for pattern analysis")
		else:
			recommended_actions.append("ALLOW: Proceed with standard processing")
			recommended_actions.append("LOG: Include in normal transaction logs")
		
		# Capture processing time
		processing_time_ms = int((perf_counter() - started) * 1000)
		
		# ========================================
		# STEP 2: LLM ONLY WRITES TEXT (NO CALCULATIONS)
		# All numbers are PRE-CALCULATED by Python above
		# ========================================
		
		from src.core.config import get_settings
		settings = get_settings()
		
		rationale = ""
		if settings.google_api_key and settings.google_api_key not in ["your_google_api_key_here", ""]:
			try:
				import google.generativeai as genai
				genai.configure(api_key=settings.google_api_key)
				model = genai.GenerativeModel('gemini-2.5-flash')
				
				# Build risk factor summary with PRE-CALCULATED values
				factor_summary = "\n".join([
					f"  - {rf['factor']}: {rf['value']} ({rf['severity']} severity, +{rf['contribution']} pts)"
					for rf in risk_factors
				]) if risk_factors else "  - No significant risk factors detected"
				
				# CRITICAL: Prompt explicitly tells LLM to use ONLY pre-calculated values
				prompt = f"""You are a Fraud Detection Analyst. Write a professional rationale for this transaction analysis.

IMPORTANT: Use ONLY the exact numbers and values provided below. Do NOT calculate any new numbers.

=== PRE-CALCULATED TRANSACTION ANALYSIS ===
- Final Decision: {decision.upper()}
- Risk Level: {risk_band.upper()}
- Alert Score: {round(alert_score * 100)}/100
- Rule-Based Score: {round(rule_score * 100)}/100 (weight: {int(rule_weight * 100)}%)
- ML Anomaly Score: {round(anomaly_score * 100)}/100 (weight: {int(anomaly_weight * 100)}%)
- Processing Time: {processing_time_ms}ms

=== PRE-CALCULATED RISK FACTORS ===
{factor_summary}

=== RULE TRIGGERS ===
{reasons}

=== YOUR TASK ===
Write a 2-3 sentence professional explanation for this fraud decision.
- Reference the EXACT numbers above (do not calculate new ones)
- Mention the most significant risk factors if any
- Be clear about why the transaction was allowed or flagged

Respond with ONLY the rationale text, nothing else."""
				
				response = model.generate_content(prompt)
				rationale = response.text.strip()
				
			except Exception as e:
				import traceback
				traceback.print_exc()
				rationale = f"Error generating AI rationale: {str(e)}. Check console for details."
		else:
			rationale = "AI Reasoning Service is currently disabled. Please provide a GOOGLE_API_KEY in .env."

		return FraudTriageOutput(
			alert_score=alert_score,
			decision=decision,
			rationale=rationale,
			policy_citations=[],
			features=features,
			risk_band=risk_band,
			rule_hits=rule_hits,
			risk_factors=risk_factors,
			anomaly_breakdown=anomaly_breakdown,
			recommended_actions=recommended_actions,
		)
