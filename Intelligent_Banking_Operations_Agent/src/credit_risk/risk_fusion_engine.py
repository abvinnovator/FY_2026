"""
Risk Fusion Engine
==================
Combines Fuzzy Logic and ML model predictions for final credit decision.

Architecture:
    Customer Data → Feature Engineering → Fuzzy Logic (10 Rules)
                                       → CatBoost ML Model
                                       → Risk Fusion → Decision
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from src.credit_risk.fuzzy_scorecard import calculate_fuzzy_score, FuzzyScorecardResult
from src.credit_risk.catboost_model import predict_credit_risk, MLPredictionResult

# Set up logger
logger = logging.getLogger("FUSION_ENGINE")
logger.setLevel(logging.INFO)


@dataclass
class FusedRiskResult:
    """Result from Risk Fusion Engine."""
    
    # Final Decision
    decision: str              # "approve", "review", "decline"
    final_score: float         # 0-100 combined score
    confidence: float          # 0-1 confidence
    
    # Component Scores
    fuzzy_score: float         # 0-100
    ml_probability: float      # 0-1 default probability
    ml_score: float            # 0-100 (inverted probability)
    
    # Risk Levels
    fuzzy_band: str
    ml_risk_level: str
    fused_risk_level: str
    
    # Explanations
    fuzzy_dominant_rules: List[str]
    ml_top_factors: List[str]
    combined_factors: List[str]
    
    # Policy
    policy_violations: List[str]
    hard_decline: bool
    hard_decline_reason: Optional[str]
    
    # Weights
    fusion_weights: Dict[str, float]


class RiskFusionEngine:
    """
    Fuses Fuzzy Logic and ML predictions.
    
    Fusion Strategy:
    1. Run Fuzzy Logic (10 rules) and ML model
    2. Convert to common 0-100 scale
    3. Weighted average
    4. Apply hard policy rules
    5. Generate final decision
    """
    
    # Decision thresholds (0-100 scale)
    APPROVE_THRESHOLD = 65
    REVIEW_THRESHOLD = 45
    
    def __init__(self, fuzzy_weight: float = 0.5, ml_weight: float = 0.5):
        total = fuzzy_weight + ml_weight
        self.fuzzy_weight = fuzzy_weight / total
        self.ml_weight = ml_weight / total
    
    def fuse(
        self,
        *,
        income: float,
        liabilities: float,
        requested_limit: float,
        delinquency_flags: List[str],
        credit_utilization: Optional[float] = None,
        employment_months: Optional[int] = None,
        credit_history_months: Optional[int] = None,
        age: Optional[int] = None,
        loan_type: str = "bnpl",
    ) -> FusedRiskResult:
        """Run both models and fuse predictions."""
        
        logger.info("=" * 60)
        logger.info("RISK FUSION ENGINE - PROCESSING")
        logger.info("=" * 60)
        
        # LOG RAW INPUT
        logger.info("STEP 1: RAW INPUT FROM FRONTEND")
        logger.info(f"  income             : ${income:,.2f}")
        logger.info(f"  liabilities        : ${liabilities:,.2f}")
        logger.info(f"  requested_limit    : ${requested_limit:,.2f}")
        logger.info(f"  delinquency_flags  : {delinquency_flags}")
        logger.info(f"  credit_utilization : {credit_utilization}%")
        
        # Feature Engineering
        dti = liabilities / income if income > 0 else 1.0
        utilization = (credit_utilization / 100.0) if credit_utilization else 0.3
        limit_ratio = (requested_limit / income) if income > 0 else 0.0
        
        # Delinquency: convert flags to numeric
        delinquency = 0
        flags_str = " ".join(delinquency_flags or []).lower()
        if "bankruptcy" in flags_str or "charge-off" in flags_str:
            delinquency = 5
        elif "90" in flags_str:
            delinquency = 3
        elif "60" in flags_str:
            delinquency = 2
        elif "30" in flags_str:
            delinquency = 1
        
        credit_history = min(6, len(delinquency_flags or []))
        
        # LOG ENGINEERED FEATURES
        logger.info("-" * 60)
        logger.info("STEP 2: FEATURE ENGINEERING (for ML Model)")
        logger.info(f"  dti            : {dti:.4f} ({dti*100:.1f}%)")
        logger.info(f"  utilization    : {utilization:.4f} ({utilization*100:.1f}%)")
        logger.info(f"  limit_ratio    : {limit_ratio:.4f}")
        logger.info(f"  delinquency    : {delinquency}")
        logger.info(f"  credit_history : {credit_history}")
        
        # ========================================
        # FUZZY LOGIC (10 Rules)
        # ========================================
        logger.info("-" * 60)
        logger.info("STEP 3: FUZZY LOGIC (10 Rules)")
        fuzzy_result = calculate_fuzzy_score(
            dti=dti,
            delinquencies=len(delinquency_flags or []),
            requested_limit_ratio=limit_ratio,
            delinquency_flags=delinquency_flags,
            credit_utilization=credit_utilization,
            employment_months=employment_months,
            credit_history_months=credit_history_months,
            age=age,
            income=income,
            loan_type=loan_type,
        )
        fuzzy_score = fuzzy_result.score
        logger.info(f"  Fuzzy Score    : {fuzzy_score:.1f}/100")
        logger.info(f"  Fuzzy Band     : {fuzzy_result.band}")
        logger.info(f"  Rules Fired    : {fuzzy_result.dominant_rules}")
        
        # ========================================
        # ML MODEL (CatBoost)
        # ========================================
        logger.info("-" * 60)
        logger.info("STEP 4: CATBOOST ML MODEL")
        ml_result = predict_credit_risk(
            dti=dti,
            utilization=utilization,
            limit_ratio=limit_ratio,
            delinquency=delinquency,
            credit_history=credit_history,
        )
        ml_probability = ml_result.default_probability
        ml_score = (1.0 - ml_probability) * 100
        logger.info(f"  Default Prob   : {ml_probability:.4f} ({ml_probability*100:.1f}%)")
        logger.info(f"  ML Score       : {ml_score:.1f}/100")
        logger.info(f"  ML Risk Level  : {ml_result.risk_level}")
        
        # ========================================
        # FUSION
        # ========================================
        logger.info("-" * 60)
        logger.info("STEP 5: FUSION (Weighted Average)")
        fused_score = (self.fuzzy_weight * fuzzy_score + self.ml_weight * ml_score)
        logger.info(f"  Fuzzy Weight   : {self.fuzzy_weight:.0%}")
        logger.info(f"  ML Weight      : {self.ml_weight:.0%}")
        logger.info(f"  Fused Score    : ({self.fuzzy_weight:.0%} × {fuzzy_score:.1f}) + ({self.ml_weight:.0%} × {ml_score:.1f}) = {fused_score:.1f}")
        
        # Confidence based on model agreement
        score_diff = abs(fuzzy_score - ml_score)
        if score_diff > 30:
            confidence = 0.6
            fused_score = min(fuzzy_score, ml_score) * 0.6 + fused_score * 0.4
        elif score_diff > 15:
            confidence = 0.8
        else:
            confidence = 0.95
        
        # ========================================
        # HARD POLICY RULES
        # ========================================
        policy_violations = list(fuzzy_result.policy_violations)
        hard_decline = False
        hard_decline_reason = None
        
        if dti >= 0.60:
            hard_decline = True
            hard_decline_reason = "DTI exceeds 60%"
            policy_violations.append("DTI-006: DTI > 60%")
        
        if "bankruptcy" in flags_str:
            hard_decline = True
            hard_decline_reason = "Bankruptcy on record"
            policy_violations.append("DEL-006: Bankruptcy")
        
        if "charge-off" in flags_str:
            hard_decline = True
            hard_decline_reason = "Charge-off on record"
            policy_violations.append("DEL-005: Charge-off")
        
        # ========================================
        # FINAL DECISION
        # ========================================
        if hard_decline:
            decision = "decline"
            fused_score = min(fused_score, 25)
            confidence = 1.0
        elif fused_score >= self.APPROVE_THRESHOLD:
            decision = "approve"
        elif fused_score >= self.REVIEW_THRESHOLD:
            decision = "review"
        else:
            decision = "decline"
        
        # Risk level
        if fused_score >= 75:
            fused_risk_level = "Low"
        elif fused_score >= 55:
            fused_risk_level = "Medium-Low"
        elif fused_score >= 40:
            fused_risk_level = "Medium"
        elif fused_score >= 25:
            fused_risk_level = "Medium-High"
        else:
            fused_risk_level = "High"
        
        # Combined factors
        combined_factors = []
        for factor in ml_result.top_risk_factors[:2]:
            combined_factors.append(f"[ML] {factor}")
        for rule in fuzzy_result.dominant_rules[:2]:
            combined_factors.append(f"[Fuzzy] {rule}")
        for pv in policy_violations[:2]:
            combined_factors.append(f"[Policy] {pv}")
        
        # LOG FINAL DECISION
        logger.info("-" * 60)
        logger.info("STEP 6: FINAL DECISION")
        logger.info(f"  Decision         : {decision.upper()}")
        logger.info(f"  Final Score      : {fused_score:.1f}/100")
        logger.info(f"  Risk Level       : {fused_risk_level}")
        logger.info(f"  Confidence       : {confidence:.0%}")
        logger.info(f"  Hard Decline     : {hard_decline}")
        logger.info(f"  Policy Violations: {policy_violations}")
        logger.info("=" * 60)
        
        return FusedRiskResult(
            decision=decision,
            final_score=round(fused_score, 1),
            confidence=round(confidence, 2),
            fuzzy_score=round(fuzzy_score, 1),
            ml_probability=round(ml_probability, 4),
            ml_score=round(ml_score, 1),
            fuzzy_band=fuzzy_result.band,
            ml_risk_level=ml_result.risk_level,
            fused_risk_level=fused_risk_level,
            fuzzy_dominant_rules=fuzzy_result.dominant_rules,
            ml_top_factors=ml_result.top_risk_factors,
            combined_factors=combined_factors,
            policy_violations=policy_violations,
            hard_decline=hard_decline,
            hard_decline_reason=hard_decline_reason,
            fusion_weights={"fuzzy": self.fuzzy_weight, "ml": self.ml_weight},
        )


def fuse_credit_risk(
    *,
    income: float,
    liabilities: float,
    requested_limit: float,
    delinquency_flags: List[str],
    credit_utilization: Optional[float] = None,
    employment_months: Optional[int] = None,
    credit_history_months: Optional[int] = None,
    age: Optional[int] = None,
    fuzzy_weight: float = 0.5,
    ml_weight: float = 0.5,
) -> FusedRiskResult:
    """Convenience function for risk fusion."""
    engine = RiskFusionEngine(fuzzy_weight=fuzzy_weight, ml_weight=ml_weight)
    return engine.fuse(
        income=income,
        liabilities=liabilities,
        requested_limit=requested_limit,
        delinquency_flags=delinquency_flags,
        credit_utilization=credit_utilization,
        employment_months=employment_months,
        credit_history_months=credit_history_months,
        age=age,
    )
