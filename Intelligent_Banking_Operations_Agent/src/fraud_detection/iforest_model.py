import numpy as np
from sklearn.ensemble import IsolationForest
from dataclasses import dataclass

@dataclass
class ModelInfo:
    loaded: bool
    n_features: int
    feature_names: list[str]

_model = None
_feature_names = ["velocity_1h_count", "velocity_1h_total", "velocity_24h_count", "velocity_24h_total", "amount_zscore", "device_novelty", "geo_novelty", "high_risk_mcc", "hour_of_day", "is_night", "first_time_mcc"]

def train_from_feature_rows(rows: list[dict]) -> ModelInfo:
    global _model
    data = []
    for r in rows:
        data.append([r.get(f, 0.0) for f in _feature_names])
    
    _model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    _model.fit(data)
    return get_model_info()

def get_model_info() -> ModelInfo:
    return ModelInfo(
        loaded=(_model is not None),
        n_features=len(_feature_names),
        feature_names=_feature_names
    )

def score_features_or_none(features: dict) -> float | None:
    if _model is None:
        return None
    try:
        data = [[float(features.get(f, 0.0)) for f in _feature_names]]
        # IsolationForest decision_function returns scores where lower is more anomalous
        # We want to return a score where higher is more anomalous, normalized roughly to [0, 1]
        raw_score = _model.decision_function(data)[0]
        # Map raw_score (typically [-0.5, 0.5]) to [0, 1]
        # Lower raw_score -> Higher anomaly score
        anomaly_score = 1.0 - (raw_score + 0.5)
        return max(0.0, min(1.0, anomaly_score))
    except Exception:
        return None
