"""
BrownBoost Credit Risk Model
=============================
Production ML model for credit default prediction.

Model: BrownBoost (AdaBoost + Decision Stumps) trained on Credit Risk Dataset
Features: dti, utilization, limit_ratio, delinquency, credit_history
Output: Default probability, risk level, top risk factors (permutation importance)
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

# Set up logger
logger = logging.getLogger("ML_MODEL")
logger.setLevel(logging.INFO)

# Lazy import - don't break route loading if dependencies missing
BROWNBOOST_AVAILABLE = False

try:
    import joblib
    BROWNBOOST_AVAILABLE = True
except ImportError:
    print("WARNING: joblib not installed. ML model predictions will be disabled.")


@dataclass
class MLPredictionResult:
    """Result from BrownBoost ML model prediction."""
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


class BrownBoostCreditModel:
    """
    BrownBoost model for credit default prediction.
    Loads pre-trained model from .pkl file.
    """
    
    MODEL_PATH = Path(__file__).parent / "brownboost_credit_model.pkl"
    
    def __init__(self):
        if not self.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.MODEL_PATH}\n"
                "Please run brownboost_train.py to generate brownboost_credit_model.pkl"
            )
        
        artifacts = joblib.load(str(self.MODEL_PATH))
        self.model = artifacts["model"]
        self.imputer = artifacts["imputer"]
        self.threshold = artifacts["threshold"]
        self._feature_names = artifacts["feature_names"]
        
        logger.info(f"BrownBoost model loaded from {self.MODEL_PATH}")
        logger.info(f"  Threshold: {self.threshold:.4f}")
        logger.info(f"  Features: {self._feature_names}")
    
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
        logger.info("ML MODEL INPUT (BrownBoost)")
        logger.info("=" * 50)
        logger.info(f"  dti            : {dti:.4f}")
        logger.info(f"  utilization    : {utilization:.4f}")
        logger.info(f"  limit_ratio    : {limit_ratio:.4f}")
        logger.info(f"  delinquency    : {delinquency}")
        logger.info(f"  credit_history : {credit_history}")
        
        # Create input array with correct feature order
        input_raw = np.array([[dti, utilization, limit_ratio, delinquency, credit_history]])
        
        # Impute (handles any NaN edge cases)
        input_imp = self.imputer.transform(input_raw)
        
        # Get probability of default (class 1)
        prob = float(self.model.predict_proba(input_imp)[0][1])
        
        # Compute feature importance via perturbation analysis
        # (BrownBoost doesn't have native SHAP, so we use sensitivity-based importance)
        feature_importance = self._compute_feature_importance(input_imp, prob)
        
        # Get top risk factors (positive importance = increases risk)
        positive_factors = {k: v for k, v in feature_importance.items() if v > 0}
        sorted_factors = sorted(positive_factors.items(), key=lambda x: x[1], reverse=True)
        top_risk_factors = [FEATURE_DESCRIPTIONS[f[0]] for f in sorted_factors[:3]]
        
        # If no positive factors found, report overall risk
        if not top_risk_factors:
            top_risk_factors = ["Overall profile within acceptable bounds"]
        
        # Determine risk level
        if prob < 0.3:
            risk_level = "Low"
        elif prob < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        # LOG OUTPUT
        logger.info("-" * 50)
        logger.info("ML MODEL OUTPUT (BrownBoost)")
        logger.info("-" * 50)
        logger.info(f"  Default Probability : {prob:.4f} ({prob*100:.1f}%)")
        logger.info(f"  Risk Level          : {risk_level}")
        logger.info(f"  Top Risk Factors    : {top_risk_factors}")
        logger.info(f"  Feature Importance  : {feature_importance}")
        logger.info("=" * 50)
        
        return MLPredictionResult(
            default_probability=round(prob, 4),
            risk_level=risk_level,
            top_risk_factors=top_risk_factors,
            feature_importance=feature_importance,
        )
    
    def _compute_feature_importance(
        self, input_imp: np.ndarray, base_prob: float
    ) -> Dict[str, float]:
        """
        Compute per-feature importance using perturbation analysis.
        For each feature, perturb it slightly and measure the change in prediction.
        This gives a SHAP-like local explanation.
        """
        importance = {}
        perturbation = 0.1  # 10% perturbation
        
        for i, name in enumerate(FEATURE_NAMES):
            perturbed = input_imp.copy()
            original_val = perturbed[0, i]
            
            # Perturb upward
            perturbed[0, i] = original_val + perturbation
            prob_up = float(self.model.predict_proba(perturbed)[0][1])
            
            # Perturb downward
            perturbed[0, i] = max(0, original_val - perturbation)
            prob_down = float(self.model.predict_proba(perturbed)[0][1])
            
            # Sensitivity: how much does the probability change?
            # Positive = this feature increases default risk at current value
            sensitivity = (prob_up - prob_down) / 2.0
            
            # Scale by the actual feature value to get contribution
            contribution = sensitivity * original_val
            importance[name] = round(contribution, 4)
        
        return importance


# Global model instance
_model: BrownBoostCreditModel = None


def get_model() -> BrownBoostCreditModel:
    """Get the global ML model instance."""
    global _model
    if _model is None:
        _model = BrownBoostCreditModel()
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
    Predict credit risk using BrownBoost model.
    
    Args:
        dti: Debt-to-income ratio (0-1)
        utilization: Credit utilization (0-1)
        limit_ratio: Requested limit / income
        delinquency: Max delinquency (0-9) 
        credit_history: Negative months count (0-6)
    
    Returns:
        MLPredictionResult
    """
    if not BROWNBOOST_AVAILABLE:
        print("ERROR: joblib module not installed - ML predictions disabled")
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
            feature_importance={},
        )
    
    model = get_model()
    return model.predict(
        dti=dti,
        utilization=utilization,
        limit_ratio=limit_ratio,
        delinquency=delinquency,
        credit_history=credit_history,
    )
