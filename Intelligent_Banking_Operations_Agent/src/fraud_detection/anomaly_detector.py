from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnomalyResult:
	score: float
	method: str


def zscore_to_anomaly(z: float) -> AnomalyResult:
	# Map z-score to [0,1] anomaly score via logistic-like squashing
	# Emphasize high z values while keeping smooth gradient
	s = 1.0 / (1.0 + pow(2.718281828, -0.9 * (abs(z) - 2.0)))
	return AnomalyResult(score=max(0.0, min(1.0, s)), method="zscore")



def choose_anomaly_score(features: dict, preferred_method: str = "zscore") -> AnomalyResult:
	"""Choose anomaly method based on configuration and availability.

	If preferred is 'iforest' and a model is loaded, use it; else fall back to zscore.
	"""
	if preferred_method == "iforest":
		try:
			from src.fraud_detection.iforest_model import score_features_or_none
			score = score_features_or_none(features)
			if score is not None:
				return AnomalyResult(score=float(score), method="iforest")
		except Exception:
			# Fallback to zscore on any failure
			pass
	# Default fallback
	return zscore_to_anomaly(float(features.get("amount_zscore", 0.0)))
