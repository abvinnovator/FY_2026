from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Thresholds(BaseModel):
    medium_band_threshold: float = 0.45
    high_band_threshold: float = 0.75

class CostMatrix(BaseModel):
    true_positive_savings: float = 100.0
    false_positive_cost: float = -20.0
    false_negative_cost: float = -200.0
    true_negative_savings: float = 0.0

class FraudConfig(BaseSettings):
    fraud_types: list[str] = ["identity_theft", "card_not_present", "account_takeover"]
    anomaly_method: str = "zscore"
    thresholds: Thresholds = Thresholds()
    cost_matrix: CostMatrix = CostMatrix()

_config = FraudConfig()

def get_config() -> FraudConfig:
    return _config

def update_config(**kwargs):
    global _config
    # Simple update logic
    for k, v in kwargs.items():
        if hasattr(_config, k):
            setattr(_config, k, v)
    return _config
