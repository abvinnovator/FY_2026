"""
CatBoost Credit Risk Model
==========================
Production ML model for credit default prediction.

Model: CatBoost trained on UCI Credit Card Dataset
Features: dti, utilization, limit_ratio, delinquency, credit_history
Output: Default probability, risk level, top risk factors (SHAP)
"""

from __future__ import annotations

import logging
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

# Lazy import catboost - don't break route loading if not installed
CATBOOST_AVAILABLE = False
CatBoostClassifier = None
Pool = None

try:
    from catboost import CatBoostClassifier, Pool
    CATBOOST_AVAILABLE = True
except ImportError:
    print("WARNING: catboost not installed. ML model predictions will be disabled.")

# Set up logger
logger = logging.getLogger("ML_MODEL")
logger.setLevel(logging.INFO)


@dataclass
class MLPredictionResult:
    """Result from CatBoost ML model prediction."""
    default_probability: float
    risk_level: str
    top_risk_factors: List[str]
    feature_importance: Dict[str, float]


# Feature names (must match training order)
FEATURE_NAMES = ["dti", "utilization", "limit_ratio", "delinquency", "credit_history"]

# Human-readable feature descriptions
FEATURE_DESCRIPTIONS = {
    "dti": "Debt-to-Income Ratio",
    "utilization": "Credit Utilization",
    "limit_ratio": "Requested Limit Ratio",
    "delinquency": "Payment Delinquency Level",
    "credit_history": "Negative Credit History Count"
}


class CatBoostCreditModel:
    """
    CatBoost model for credit default prediction.
    Loads pre-trained model from .cbm file.
    """
    
    MODEL_PATH = Path(__file__).parent / "catboost_credit_model.cbm"
    
    def __init__(self):
        if not self.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.MODEL_PATH}\n"
                "Please run the notebook to generate catboost_credit_model.cbm"
            )
        
        self.model = CatBoostClassifier()
        self.model.load_model(str(self.MODEL_PATH))
    
    def predict(
        self,
        *,
        dti: float,
        utilization: float,
        limit_ratio: float,
        delinquency: int,
        credit_history: int,
    ) -> MLPredictionResult:
        """
        Predict credit default probability.
        
        Args:
            dti: Debt-to-income ratio (0-1)
            utilization: Credit utilization (0-1)
            limit_ratio: Requested limit as ratio of income
            delinquency: Maximum delinquency level (0-9)
            credit_history: Count of months with late payments (0-6)
        
        Returns:
            MLPredictionResult with probability, risk level, and top factors
        """
        
        # LOG INPUT
        logger.info("=" * 50)
        logger.info("ML MODEL INPUT")
        logger.info("=" * 50)
        logger.info(f"  dti            : {dti:.4f}")
        logger.info(f"  utilization    : {utilization:.4f}")
        logger.info(f"  limit_ratio    : {limit_ratio:.4f}")
        logger.info(f"  delinquency    : {delinquency}")
        logger.info(f"  credit_history : {credit_history}")
        
        # Create input DataFrame with correct column order
        input_df = pd.DataFrame([{
            "dti": dti,
            "utilization": utilization,
            "limit_ratio": limit_ratio,
            "delinquency": delinquency,
            "credit_history": credit_history
        }])[FEATURE_NAMES]
        
        # Get probability
        prob = float(self.model.predict_proba(input_df)[0][1])
        
        # Get SHAP values
        pool = Pool(input_df)
        shap_values = self.model.get_feature_importance(pool, type="ShapValues")
        shap_contrib = shap_values[0][:-1]  # Remove base value
        
        # Build feature importance dict
        feature_importance = {
            FEATURE_NAMES[i]: float(shap_contrib[i]) 
            for i in range(len(FEATURE_NAMES))
        }
        
        # Get top risk factors (positive SHAP = increases risk)
        positive_factors = {k: v for k, v in feature_importance.items() if v > 0}
        sorted_factors = sorted(positive_factors.items(), key=lambda x: x[1], reverse=True)
        top_risk_factors = [FEATURE_DESCRIPTIONS[f[0]] for f in sorted_factors[:3]]
        
        # Determine risk level
        if prob < 0.3:
            risk_level = "Low"
        elif prob < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # LOG OUTPUT
        logger.info("-" * 50)
        logger.info("ML MODEL OUTPUT")
        logger.info("-" * 50)
        logger.info(f"  Default Probability : {prob:.4f} ({prob*100:.1f}%)")
        logger.info(f"  Risk Level          : {risk_level}")
        logger.info(f"  Top Risk Factors    : {top_risk_factors}")
        logger.info(f"  SHAP Values         : {feature_importance}")
        logger.info("=" * 50)
        
        return MLPredictionResult(
            default_probability=round(prob, 4),
            risk_level=risk_level,
            top_risk_factors=top_risk_factors,
            feature_importance=feature_importance,
        )


# Global model instance
_model: CatBoostCreditModel = None


def get_model() -> CatBoostCreditModel:
    """Get the global ML model instance."""
    global _model
    if _model is None:
        _model = CatBoostCreditModel()
    return _model


def predict_credit_risk(
    *,
    dti: float,
    utilization: float,
    limit_ratio: float,
    delinquency: int,
    credit_history: int,
) -> MLPredictionResult:
    """
    Predict credit risk using CatBoost model.
    
    Args:
        dti: Debt-to-income ratio (0-1)
        utilization: Credit utilization (0-1)
        limit_ratio: Requested limit / income
        delinquency: Max delinquency (0-9) 
        credit_history: Negative months count (0-6)
    
    Returns:
        MLPredictionResult
    """
    if not CATBOOST_AVAILABLE:
        print("ERROR: catboost module not installed - ML predictions disabled")
        # Return a placeholder result based on simple heuristics
        risk_score = min(1.0, dti + utilization * 0.3 + delinquency * 0.1)
        if risk_score > 0.6:
            risk_level = "High"
        elif risk_score > 0.3:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        return MLPredictionResult(
            default_probability=risk_score,
            risk_level=risk_level,
            top_risk_factors=["ML model not available - using heuristic"],
            feature_contributions={},
            model_version="heuristic-fallback"
        )
    
    model = get_model()
    return model.predict(
        dti=dti,
        utilization=utilization,
        limit_ratio=limit_ratio,
        delinquency=delinquency,
        credit_history=credit_history,
    )
