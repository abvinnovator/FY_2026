from __future__ import annotations

from typing import Tuple

from src.fraud_detection.rules_runtime import apply_runtime_rules

def evaluate_rules(features: dict) -> Tuple[float, list[str]]:
	"""Simple, explainable rule-based scoring.

	Returns (rule_score, rule_hits)
	"""
	rule_score = 0.0
	rule_hits: list[str] = []

	if features.get("amount_zscore", 0.0) >= 3.5:
		rule_score += 0.4
		rule_hits.append(f"amount spike {features['amount_zscore']:.1f}σ above mean")

	if features.get("velocity_1h_count", 0.0) >= 5:
		rule_score += 0.2
		rule_hits.append("high velocity in last 1h")

	if features.get("device_novelty", 0.0) >= 1.0:
		rule_score += 0.2
		rule_hits.append("new device detected")

	if features.get("geo_novelty", 0.0) >= 1.0:
		rule_score += 0.1
		rule_hits.append("new geo detected")

	if features.get("high_risk_mcc", 0.0) >= 1.0:
		rule_score += 0.2
		rule_hits.append("high-risk MCC")

	# Simple time-of-day risk
	if features.get("is_night", 0.0) >= 1.0:
		rule_score += 0.05
		rule_hits.append("night-time transaction")

	# First-time MCC behavior
	if features.get("first_time_mcc", 0.0) >= 1.0:
		rule_score += 0.1
		rule_hits.append("first-time MCC for account")

	# Runtime rules (accepted suggestions) applied last
	extra, extra_hits = apply_runtime_rules(features)
	rule_score += extra
	rule_hits.extend(extra_hits)

	return min(rule_score, 1.0), rule_hits


