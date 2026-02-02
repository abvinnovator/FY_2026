"""
Fuzzy Logic Credit Scoring System
=================================
Implements a Mamdani-style fuzzy inference system for credit risk assessment.

Uses 10 fuzzy rules based on real banking policies:
- RBI (Reserve Bank of India) Guidelines
- Basel III Capital Adequacy Framework  
- OCC (Office of the Comptroller of the Currency) Handbook

Fuzzy Logic Approach:
- Converts crisp inputs to fuzzy membership degrees
- Applies fuzzy rules (IF-THEN statements)
- Aggregates rule outputs
- Defuzzifies to get crisp credit score

Author: Banking Operations AI Agent
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import json
from pathlib import Path

# Try to import skfuzzy, fallback to numpy-based implementation if not available
try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    SKFUZZY_AVAILABLE = True
except ImportError:
    SKFUZZY_AVAILABLE = False
    print("WARNING: scikit-fuzzy not installed. Using simplified fuzzy logic implementation.")


@dataclass
class FuzzyRuleResult:
    """Result of a single fuzzy rule evaluation."""
    rule_id: str
    rule_name: str
    description: str
    firing_strength: float  # 0-1, how strongly this rule fired
    contribution: float     # Impact on final score
    policy_reference: str   # e.g., "RBI-DTI-001"


@dataclass
class FuzzyMembershipDebug:
    """Debug info showing membership degrees for each input."""
    variable: str
    value: float
    memberships: Dict[str, float]  # e.g., {"low": 0.3, "medium": 0.7, "high": 0.0}


@dataclass 
class FuzzyScorecardResult:
    """Complete result from fuzzy credit scoring."""
    score: float                              # 0-100 credit score
    band: str                                 # "excellent", "good", "fair", "poor"
    decision: str                             # "approve", "review", "decline"
    rule_results: List[FuzzyRuleResult]       # Individual rule evaluations
    membership_debug: List[FuzzyMembershipDebug]  # Show how inputs were fuzzified
    dominant_rules: List[str]                 # Top 3 rules that influenced decision
    policy_violations: List[str]              # Any hard policy violations


# ============================================================================
# FUZZY MEMBERSHIP FUNCTIONS (Triangular and Trapezoidal)
# ============================================================================

def trimf(x: float, params: Tuple[float, float, float]) -> float:
    """Triangular membership function.
    
    Args:
        x: Input value
        params: (a, b, c) where a=left foot, b=peak, c=right foot
    
    Returns:
        Membership degree [0, 1]
    """
    a, b, c = params
    if x <= a or x >= c:
        return 0.0
    elif a < x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    else:  # b < x < c
        return (c - x) / (c - b) if c != b else 1.0


def trapmf(x: float, params: Tuple[float, float, float, float]) -> float:
    """Trapezoidal membership function.
    
    Args:
        x: Input value  
        params: (a, b, c, d) where a=left foot, b=left shoulder, c=right shoulder, d=right foot
    
    Returns:
        Membership degree [0, 1]
    """
    a, b, c, d = params
    if x <= a or x >= d:
        return 0.0
    elif a < x < b:
        return (x - a) / (b - a) if b != a else 1.0
    elif b <= x <= c:
        return 1.0
    else:  # c < x < d
        return (d - x) / (d - c) if d != c else 1.0


# ============================================================================
# FUZZY INPUT VARIABLES WITH MEMBERSHIP FUNCTIONS
# ============================================================================

class FuzzyVariable:
    """Represents a fuzzy linguistic variable with membership functions."""
    
    def __init__(self, name: str, universe: Tuple[float, float]):
        self.name = name
        self.universe = universe
        self.mfs: Dict[str, Tuple[str, tuple]] = {}  # term -> (type, params)
    
    def add_mf(self, term: str, mf_type: str, params: tuple):
        """Add a membership function for a linguistic term."""
        self.mfs[term] = (mf_type, params)
    
    def fuzzify(self, x: float) -> Dict[str, float]:
        """Convert crisp value to membership degrees for all terms."""
        memberships = {}
        for term, (mf_type, params) in self.mfs.items():
            if mf_type == "trimf":
                memberships[term] = trimf(x, params)
            elif mf_type == "trapmf":
                memberships[term] = trapmf(x, params)
        return memberships


# ============================================================================
# FUZZY CREDIT SCORING ENGINE
# ============================================================================

class FuzzyCreditScorer:
    """
    Fuzzy Logic Credit Scoring System with 10 Rules.
    
    Based on Mamdani fuzzy inference:
    1. Fuzzification: Convert inputs to fuzzy membership degrees
    2. Rule Evaluation: Apply fuzzy rules with AND/OR operations
    3. Aggregation: Combine rule outputs
    4. Defuzzification: Convert to crisp score
    """
    
    def __init__(self):
        self._setup_variables()
        self._setup_rules()
    
    def _setup_variables(self):
        """Define fuzzy input and output variables."""
        
        # ========== INPUT VARIABLE 1: DTI (Debt-to-Income) ==========
        # Range: 0% to 100%
        self.dti = FuzzyVariable("DTI", (0, 100))
        self.dti.add_mf("excellent", "trapmf", (0, 0, 20, 28))      # DTI < 28%
        self.dti.add_mf("good", "trimf", (25, 32, 40))              # Around 32%
        self.dti.add_mf("moderate", "trimf", (36, 43, 50))          # Around 43%  
        self.dti.add_mf("high", "trimf", (45, 52, 60))              # Around 52%
        self.dti.add_mf("critical", "trapmf", (55, 60, 100, 100))   # DTI > 60%
        
        # ========== INPUT VARIABLE 2: Credit Utilization ==========
        # Range: 0% to 100%
        self.utilization = FuzzyVariable("CreditUtilization", (0, 100))
        self.utilization.add_mf("excellent", "trapmf", (0, 0, 20, 30))
        self.utilization.add_mf("good", "trimf", (25, 40, 55))
        self.utilization.add_mf("high", "trimf", (50, 70, 85))
        self.utilization.add_mf("critical", "trapmf", (80, 90, 100, 100))
        
        # ========== INPUT VARIABLE 3: Payment History (Delinquency Days) ==========
        # Range: 0 to 180 days past due
        self.delinquency = FuzzyVariable("DelinquencyDays", (0, 180))
        self.delinquency.add_mf("clean", "trapmf", (0, 0, 0, 5))
        self.delinquency.add_mf("minor", "trimf", (0, 15, 35))       # Around 30 DPD
        self.delinquency.add_mf("moderate", "trimf", (30, 60, 75))   # Around 60 DPD
        self.delinquency.add_mf("serious", "trimf", (60, 90, 120))   # Around 90 DPD
        self.delinquency.add_mf("severe", "trapmf", (90, 120, 180, 180))
        
        # ========== INPUT VARIABLE 4: Credit History Length (Months) ==========
        # Range: 0 to 240 months (20 years)
        self.history_length = FuzzyVariable("CreditHistoryMonths", (0, 240))
        self.history_length.add_mf("thin", "trapmf", (0, 0, 3, 12))
        self.history_length.add_mf("new", "trimf", (6, 18, 36))
        self.history_length.add_mf("established", "trimf", (24, 60, 84))
        self.history_length.add_mf("mature", "trapmf", (72, 120, 240, 240))
        
        # ========== INPUT VARIABLE 5: Employment Stability (Months) ==========
        # Range: 0 to 120 months (10 years)
        self.employment = FuzzyVariable("EmploymentMonths", (0, 120))
        self.employment.add_mf("unstable", "trapmf", (0, 0, 3, 9))
        self.employment.add_mf("short", "trimf", (6, 12, 24))
        self.employment.add_mf("stable", "trimf", (18, 36, 60))
        self.employment.add_mf("very_stable", "trapmf", (48, 72, 120, 120))
        
        # ========== INPUT VARIABLE 6: Income Level (Monthly USD) ==========
        # Range: 0 to 50000
        self.income = FuzzyVariable("MonthlyIncome", (0, 50000))
        self.income.add_mf("low", "trapmf", (0, 0, 2000, 4000))
        self.income.add_mf("moderate", "trimf", (3000, 6000, 10000))
        self.income.add_mf("good", "trimf", (8000, 15000, 25000))
        self.income.add_mf("high", "trapmf", (20000, 30000, 50000, 50000))
        
        # ========== INPUT VARIABLE 7: Requested Limit Ratio ==========
        # Range: 0% to 300% of income
        self.limit_ratio = FuzzyVariable("RequestedLimitRatio", (0, 300))
        self.limit_ratio.add_mf("conservative", "trapmf", (0, 0, 15, 30))
        self.limit_ratio.add_mf("reasonable", "trimf", (20, 40, 60))
        self.limit_ratio.add_mf("stretched", "trimf", (50, 80, 120))
        self.limit_ratio.add_mf("excessive", "trapmf", (100, 150, 300, 300))
        
        # ========== INPUT VARIABLE 8: Age ==========
        # Range: 18 to 80 years
        self.age = FuzzyVariable("Age", (18, 80))
        self.age.add_mf("young", "trapmf", (18, 18, 22, 28))
        self.age.add_mf("prime", "trimf", (25, 40, 55))
        self.age.add_mf("mature", "trapmf", (50, 60, 80, 80))
        
        # ========== OUTPUT VARIABLE: Credit Score ==========
        # Range: 0 to 100
        self.credit_score = FuzzyVariable("CreditScore", (0, 100))
        self.credit_score.add_mf("very_poor", "trapmf", (0, 0, 15, 30))
        self.credit_score.add_mf("poor", "trimf", (20, 35, 50))
        self.credit_score.add_mf("fair", "trimf", (40, 55, 70))
        self.credit_score.add_mf("good", "trimf", (60, 75, 85))
        self.credit_score.add_mf("excellent", "trapmf", (75, 90, 100, 100))
    
    def _setup_rules(self):
        """
        Load 10 fuzzy rules from JSON file.
        
        Each rule follows: IF (conditions) THEN (credit_score is TERM)
        """
        rules_path = Path(__file__).parent / "rules.json"
        try:
            with open(rules_path, "r") as f:
                rules_data = json.load(f)
            # Convert lists to tuples where necessary (json.load gives lists)
            self.rules = []
            for rule in rules_data:
                processed_rule = rule.copy()
                processed_rule["conditions"] = [tuple(c) for c in rule["conditions"]]
                if "conditions_alt" in rule:
                    processed_rule["conditions_alt"] = [tuple(c) for c in rule["conditions_alt"]]
                processed_rule["consequent"] = tuple(rule["consequent"])
                self.rules.append(processed_rule)
        except Exception as e:
            print(f"ERROR: Could not load fuzzy rules from {rules_path}: {e}")
            self.rules = []
    
    def _get_variable(self, name: str) -> FuzzyVariable:
        """Get fuzzy variable by name."""
        mapping = {
            "dti": self.dti,
            "utilization": self.utilization,
            "delinquency": self.delinquency,
            "history_length": self.history_length,
            "employment": self.employment,
            "income": self.income,
            "limit_ratio": self.limit_ratio,
            "age": self.age,
            "credit_score": self.credit_score,
        }
        return mapping.get(name)
    
    def _evaluate_rule(self, rule: dict, memberships: Dict[str, Dict[str, float]]) -> Tuple[float, str]:
        """
        Evaluate a single fuzzy rule.
        
        Returns:
            Tuple of (firing_strength, output_term)
        """
        # Get antecedent firing strength (AND = min, OR = max)
        logic = rule.get("logic", "AND")
        
        strengths = []
        for var_name, term in rule["conditions"]:
            if var_name in memberships and term in memberships[var_name]:
                strengths.append(memberships[var_name][term])
            else:
                strengths.append(0.0)
        
        # Handle OR with alternative conditions
        if "conditions_alt" in rule:
            alt_strengths = []
            for var_name, term in rule["conditions_alt"]:
                if var_name in memberships and term in memberships[var_name]:
                    alt_strengths.append(memberships[var_name][term])
            if alt_strengths:
                strengths.append(max(alt_strengths))
        
        if logic == "OR":
            firing_strength = max(strengths) if strengths else 0.0
        else:  # AND
            firing_strength = min(strengths) if strengths else 0.0
        
        # Apply rule weight
        firing_strength *= rule.get("weight", 1.0)
        firing_strength = min(1.0, firing_strength)  # Cap at 1
        
        output_term = rule["consequent"][1]
        return firing_strength, output_term
    
    def _defuzzify(self, output_activations: Dict[str, float]) -> float:
        """
        Defuzzify using centroid method.
        
        Args:
            output_activations: Dict mapping output terms to their activation levels
        
        Returns:
            Crisp score (0-100)
        """
        # Define centroid values for each output term
        centroids = {
            "very_poor": 15,
            "poor": 35,
            "fair": 55,
            "good": 75,
            "excellent": 92
        }
        
        numerator = 0.0
        denominator = 0.0
        
        for term, activation in output_activations.items():
            if term in centroids and activation > 0:
                numerator += centroids[term] * activation
                denominator += activation
        
        if denominator > 0:
            return numerator / denominator
        else:
            return 50.0  # Default neutral score
    
    def score(
        self,
        *,
        dti: float,                          # As percentage (0-100)
        credit_utilization: float = 30.0,    # As percentage (0-100)  
        delinquency_days: int = 0,           # Days past due
        credit_history_months: int = 36,     # Months
        employment_months: int = 24,         # Months
        income: float = 5000.0,              # Monthly USD
        requested_limit_ratio: float = 40.0, # As percentage
        age: int = 35,
        loan_type: str = "bnpl",
    ) -> FuzzyScorecardResult:
        """
        Calculate fuzzy credit score.
        
        Args:
            dti: Debt-to-income ratio as percentage (0-100)
            credit_utilization: Credit utilization as percentage (0-100)
            delinquency_days: Maximum days past due on any account
            credit_history_months: Length of credit history in months
            employment_months: Months at current employer
            income: Monthly income in USD
            requested_limit_ratio: Requested limit as % of income
            age: Applicant age
        
        Returns:
            FuzzyScorecardResult with score, decision, and rule analysis
        """
        
        # ========================================
        # STEP 1: FUZZIFICATION
        # ========================================
        
        memberships = {
            "dti": self.dti.fuzzify(dti),
            "utilization": self.utilization.fuzzify(credit_utilization),
            "delinquency": self.delinquency.fuzzify(delinquency_days),
            "history_length": self.history_length.fuzzify(credit_history_months),
            "employment": self.employment.fuzzify(employment_months),
            "income": self.income.fuzzify(income),
            "limit_ratio": self.limit_ratio.fuzzify(requested_limit_ratio),
            "age": self.age.fuzzify(age),
        }
        
        # Create debug info
        membership_debug = []
        for var_name, var_memberships in memberships.items():
            # Get the actual input value
            input_values = {
                "dti": dti,
                "utilization": credit_utilization,
                "delinquency": delinquency_days,
                "history_length": credit_history_months,
                "employment": employment_months,
                "income": income,
                "limit_ratio": requested_limit_ratio,
                "age": age
            }
            membership_debug.append(FuzzyMembershipDebug(
                variable=var_name,
                value=input_values.get(var_name, 0),
                memberships={k: round(v, 3) for k, v in var_memberships.items()}
            ))
        
        # ========================================
        # STEP 2: RULE EVALUATION
        # ========================================
        
        output_activations: Dict[str, float] = {
            "very_poor": 0.0,
            "poor": 0.0,
            "fair": 0.0,
            "good": 0.0,
            "excellent": 0.0
        }
        
        rule_results = []
        
        for rule in self.rules:
            firing_strength, output_term = self._evaluate_rule(rule, memberships)
            
            # Aggregate using MAX (standard Mamdani)
            output_activations[output_term] = max(
                output_activations[output_term],
                firing_strength
            )
            
            # Record rule result
            rule_results.append(FuzzyRuleResult(
                rule_id=rule["id"],
                rule_name=rule["name"],
                description=rule["description"],
                firing_strength=round(firing_strength, 3),
                contribution=round(firing_strength * 100, 1),
                policy_reference=rule["policy"]
            ))
        
        # ========================================
        # STEP 3: DEFUZZIFICATION
        # ========================================
        
        final_score = self._defuzzify(output_activations)
        final_score = round(max(0.0, min(100.0, final_score)), 1)
        
        # ========================================
        # STEP 4: DETERMINE DECISION
        # ========================================
        
        policy_violations = []
        
        # Hard policy checks (override fuzzy score)
        if dti >= 60:
            policy_violations.append("DTI exceeds 60% hard limit (Policy DTI-006)")
            final_score = min(final_score, 25)
        
        if delinquency_days >= 90:
            policy_violations.append("90+ DPD serious delinquency (Policy DEL-003)")
            final_score = min(final_score, 30)
        
        # ========================================
        # REAL-WORLD PRODUCT-SPECIFIC RULES
        # ========================================
        
        # ===== BNPL (Buy Now Pay Later) RULES =====
        # BNPL is transaction-specific, not profile-based
        # - Small purchase limits (typically 50-100% of monthly income MAX)
        # - Strict on existing defaults
        # - No "prime applicant" bonus - everyone is equal
        if loan_type == "bnpl":
            # BNPL Rule 1: Max limit is typically 50-100% of income
            bnpl_max_limit = 100  # 100% of monthly income is MAX
            if requested_limit_ratio > bnpl_max_limit:
                policy_violations.append(f"BNPL limit {requested_limit_ratio:.0f}% exceeds typical BNPL max ({bnpl_max_limit}%) (Policy BNPL-001)")
                final_score = min(final_score, 35)
            
            # BNPL Rule 2: Any delinquency = decline (previous defaults)
            if delinquency_days > 0:
                policy_violations.append(f"Previous delinquency ({delinquency_days} days) - BNPL requires clean history (Policy BNPL-002)")
                final_score = min(final_score, 30)
            
            # BNPL Rule 3: High utilization = decline (existing debt stress)
            if credit_utilization > 70:
                policy_violations.append(f"High utilization ({credit_utilization:.0f}%) indicates existing debt stress (Policy BNPL-003)")
                final_score = min(final_score, 40)
            
            # BNPL Rule 4: Age check (must be 18+)
            if age < 18:
                policy_violations.append("Age below 18 - BNPL requires adult applicant (Policy BNPL-004)")
                final_score = min(final_score, 0)
        
        # ===== PERSONAL LOAN RULES =====
        # - Requires income verification
        # - Employment stability important
        # - Credit score preferences (reflected in history length)
        # - DTI is critical
        elif loan_type == "personal_loan":
            # PL Rule 1: Minimum income requirement (₹10k/$1000+ monthly)
            if income < 1000:
                policy_violations.append(f"Income ${income:.0f} below minimum $1000 for personal loan (Policy PL-001)")
                final_score = min(final_score, 35)
            
            # PL Rule 2: Employment stability (typically 6+ months preferred)
            if employment_months < 6:
                policy_violations.append(f"Employment {employment_months} months - personal loan requires 6+ months stability (Policy PL-002)")
                final_score = min(final_score, 45)
            
            # PL Rule 3: Credit history (2+ years preferred)
            if credit_history_months < 12:
                policy_violations.append(f"Credit history {credit_history_months} months - thin file risk (Policy PL-003)")
                final_score = min(final_score, 50)
            
            # PL Rule 4: DTI check (important for unsecured loans)
            if dti > 50:
                policy_violations.append(f"DTI {dti:.0f}% too high for personal loan - max 50% preferred (Policy PL-004)")
                final_score = min(final_score, 40)
            
            # PL Rule 5: Reasonable limit (typically 2-4x monthly income for prime)
            # Prime applicant can get up to 4x, others 2x
            is_prime_pl = (dti <= 35 and credit_utilization <= 40 and 
                          delinquency_days == 0 and credit_history_months >= 24 and
                          employment_months >= 12 and income >= 3000)
            pl_max_ratio = 400 if is_prime_pl else 200
            
            if requested_limit_ratio > pl_max_ratio:
                policy_violations.append(f"Limit request {requested_limit_ratio:.0f}% exceeds {pl_max_ratio}% max for personal loan (Policy PL-005)")
                final_score = min(final_score, 35)
            elif is_prime_pl and final_score < 70:
                # Prime PL applicant bonus
                final_score = max(final_score, 75)
        
        # ===== CREDIT CARD RULES =====
        # - Good credit history is critical
        # - Utilization ratio very important
        # - Late payments = decline
        else:  # credit_card
            # CC Rule 1: Credit history required (at least 6 months)
            if credit_history_months < 6:
                policy_violations.append(f"Credit history {credit_history_months} months - credit card requires established history (Policy CC-001)")
                final_score = min(final_score, 40)
            
            # CC Rule 2: Existing utilization check (max 70% preferred)
            if credit_utilization > 70:
                policy_violations.append(f"Utilization {credit_utilization:.0f}% too high - credit card max 70% preferred (Policy CC-002)")
                final_score = min(final_score, 45)
            
            # CC Rule 3: Poor repayment history = decline
            if delinquency_days >= 30:
                policy_violations.append(f"Late payment history ({delinquency_days} days) - credit card requires good repayment (Policy CC-003)")
                final_score = min(final_score, 35)
            
            # CC Rule 4: Limit based on profile
            is_prime_cc = (dti <= 40 and credit_utilization <= 50 and 
                          delinquency_days == 0 and credit_history_months >= 12)
            cc_max_ratio = 300 if is_prime_cc else 150
            
            if requested_limit_ratio > cc_max_ratio:
                policy_violations.append(f"Limit request {requested_limit_ratio:.0f}% exceeds {cc_max_ratio}% max for credit card (Policy CC-004)")
                final_score = min(final_score, 40)
            elif is_prime_cc and final_score < 70:
                # Prime CC applicant bonus
                final_score = max(final_score, 70)
        
        # ===== COMMON RULES (ALL PRODUCTS) =====
        # Critical utilization check
        if credit_utilization >= 90:
            policy_violations.append(f"Credit utilization {credit_utilization:.0f}% exceeds 90% critical threshold (Policy UTL-005)")
            final_score = min(final_score, 35)
        
        # Determine band and decision
        if final_score >= 75:
            band = "excellent"
            decision = "approve"
        elif final_score >= 60:
            band = "good" 
            decision = "approve"
        elif final_score >= 45:
            band = "fair"
            decision = "review"
        else:
            band = "poor"
            decision = "decline"
        
        # Override decision if policy violations exist
        if policy_violations:
            decision = "decline"
            band = "poor"
        
        # Find dominant rules (top 3 by firing strength)
        sorted_rules = sorted(rule_results, key=lambda r: r.firing_strength, reverse=True)
        dominant_rules = [f"{r.rule_id}: {r.rule_name} (strength: {r.firing_strength:.2f})" 
                        for r in sorted_rules[:3] if r.firing_strength > 0]
        
        return FuzzyScorecardResult(
            score=final_score,
            band=band,
            decision=decision,
            rule_results=rule_results,
            membership_debug=membership_debug,
            dominant_rules=dominant_rules,
            policy_violations=policy_violations
        )


# ============================================================================
# CONVENIENCE FUNCTION FOR INTEGRATION
# ============================================================================

def calculate_fuzzy_score(
    *,
    dti: float,
    delinquencies: int = 0,
    requested_limit_ratio: float | None = None,
    delinquency_flags: list[str] | None = None,
    credit_utilization: float | None = None,
    employment_months: int | None = None,
    credit_history_months: int | None = None,
    age: int | None = None,
    income: float | None = None,
    loan_type: str = "bnpl",
) -> FuzzyScorecardResult:
    """
    Convenience function to calculate fuzzy credit score.
    
    This wraps the FuzzyCreditScorer for easy integration with existing code.
    Converts dti from 0-1 scale to 0-100 percentage.
    """
    scorer = FuzzyCreditScorer()
    
    # Convert DTI from decimal (0-1) to percentage (0-100)
    dti_percent = dti * 100 if dti <= 1.0 else dti
    
    # Map delinquency flags to days
    delinquency_days = 0
    if delinquency_flags:
        flag_str = " ".join(delinquency_flags).lower()
        if "90" in flag_str:
            delinquency_days = 90
        elif "60" in flag_str:
            delinquency_days = 60
        elif "30" in flag_str:
            delinquency_days = 30
        if "bankruptcy" in flag_str or "charge-off" in flag_str:
            delinquency_days = 180  # Severe
    
    # Use delinquencies count as fallback
    if delinquency_days == 0 and delinquencies > 0:
        delinquency_days = delinquencies * 30  # Estimate
    
    return scorer.score(
        dti=dti_percent,
        credit_utilization=credit_utilization * 100 if credit_utilization and credit_utilization <= 1 else (credit_utilization or 30.0),
        delinquency_days=delinquency_days,
        credit_history_months=credit_history_months or 36,
        employment_months=employment_months or 24,
        income=income or 5000.0,
        # Limit ratio: convert decimal to percentage (e.g., 28.73 -> 2873%)
        requested_limit_ratio=(requested_limit_ratio * 100) if requested_limit_ratio and requested_limit_ratio <= 3.0 else (requested_limit_ratio or 40.0),
        age=age or 35,
        loan_type=loan_type,
    )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the fuzzy scoring system
    print("=" * 60)
    print("FUZZY CREDIT SCORING SYSTEM TEST")
    print("=" * 60)
    
    test_cases = [
        {"dti": 0.25, "delinquencies": 0, "name": "Excellent Applicant"},
        {"dti": 0.45, "delinquencies": 1, "name": "Moderate Risk"},
        {"dti": 0.65, "delinquencies": 3, "name": "High Risk"},
    ]
    
    for tc in test_cases:
        print(f"\n{'='*40}")
        print(f"TEST: {tc['name']}")
        print(f"{'='*40}")
        
        result = calculate_fuzzy_score(
            dti=tc["dti"],
            delinquencies=tc["delinquencies"],
        )
        
        print(f"Score: {result.score}/100")
        print(f"Band: {result.band}")
        print(f"Decision: {result.decision}")
        print(f"\nDominant Rules:")
        for rule in result.dominant_rules:
            print(f"  - {rule}")
        if result.policy_violations:
            print(f"\nPolicy Violations:")
            for pv in result.policy_violations:
                print(f"  ⚠ {pv}")
