from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PolicyViolation:
	"""Represents a specific policy that was violated."""
	code: str  # e.g., "DTI-001"
	policy_name: str  # e.g., "Debt-to-Income Ratio Policy"
	section: str  # e.g., "Section 1.1"
	threshold: str  # e.g., "DTI > 50% requires senior review"
	actual_value: str  # e.g., "Your DTI: 55%"
	severity: str  # 'info', 'warning', 'violation', 'hard_decline'


@dataclass
class FactorContribution:
	"""Represents how much each factor contributed to the final score."""
	factor_name: str
	impact: float  # Negative means penalty, positive means bonus
	description: str
	severity: str  # 'low', 'medium', 'high', 'critical'
	policy_code: Optional[str] = None  # Link to policy violation


@dataclass
class ScorecardResult:
	score: float
	band: str
	contributors: list[str]
	factor_breakdown: list[FactorContribution] = field(default_factory=list)
	policy_violations: list[PolicyViolation] = field(default_factory=list)
	base_score: float = 1.0
	hard_decline: bool = False
	hard_decline_reason: Optional[str] = None


def calculate_scorecard(
	*, 
	dti: float, 
	delinquencies: int, 
	requested_limit_ratio: float | None,
	# New optional parameters for enhanced analysis
	delinquency_flags: list[str] | None = None,
	credit_utilization: float | None = None,
	employment_months: int | None = None,
	credit_history_months: int | None = None,
	age: int | None = None,
	income: float | None = None,
	has_bankruptcy: bool = False,
	has_writeoff: bool = False,
	loan_type: str | None = None,
) -> ScorecardResult:
	"""
	Enhanced scorecard with comprehensive credit risk rules.
	Based on real banking policies (RBI, Basel III, OCC guidelines).
	
	Returns:
		- Score (0-1 scale, converted to 0-100 for display)
		- Factor contributions with severity
		- Policy violations with codes for LLM citation
	"""
	base_score = 1.0
	score = base_score
	contributors: list[str] = []
	factor_breakdown: list[FactorContribution] = []
	policy_violations: list[PolicyViolation] = []
	hard_decline = False
	hard_decline_reason = None
	
	delinquency_flags = delinquency_flags or []
	
	# =====================================================
	# RULE 1: HARD DECLINE CHECKS (Automatic Rejections)
	# These override all other scoring
	# =====================================================
	
	# Rule 1.1: Bankruptcy Check (Policy DEL-006)
	if has_bankruptcy or "bankruptcy" in [f.lower() for f in delinquency_flags]:
		hard_decline = True
		hard_decline_reason = "Bankruptcy on record - Policy DEL-006"
		policy_violations.append(PolicyViolation(
			code="DEL-006",
			policy_name="Bankruptcy Policy",
			section="Section 2.1",
			threshold="Bankruptcy: Hard decline for 7-10 years",
			actual_value="Bankruptcy detected on credit file",
			severity="hard_decline"
		))
	
	# Rule 1.2: Write-off/Charge-off Check (Policy DEL-005)
	if has_writeoff or "charge-off" in [f.lower() for f in delinquency_flags]:
		hard_decline = True
		hard_decline_reason = "Charge-off on record - Policy DEL-005"
		policy_violations.append(PolicyViolation(
			code="DEL-005",
			policy_name="Write-off Policy",
			section="Section 2.1",
			threshold="Written-off/Charge-off: Hard decline for 7 years",
			actual_value="Charge-off detected on credit file",
			severity="hard_decline"
		))
	
	# Rule 1.3: DTI > 60% Hard Decline (Policy DTI-006)
	if dti >= 0.60:
		hard_decline = True
		hard_decline_reason = f"DTI of {round(dti*100)}% exceeds 60% hard limit - Policy DTI-006"
		policy_violations.append(PolicyViolation(
			code="DTI-006",
			policy_name="Maximum DTI Policy",
			section="Section 1.1",
			threshold="DTI > 60%: Hard Decline - No exceptions permitted",
			actual_value=f"Your DTI: {round(dti*100)}%",
			severity="hard_decline"
		))
	
	# Rule 1.4: Product-Specific Limit and Profile Checks
	# Real-world banking rules for each product type
	
	util_pct = (credit_utilization if credit_utilization and credit_utilization > 1 else (credit_utilization or 0) * 100)
	emp_months = employment_months or 0
	hist_months = credit_history_months or 0
	applicant_income = income or 0
	
	if loan_type == "bnpl":
		# BNPL: Transaction-specific, strict limits
		bnpl_max_ratio = 1.0  # 100% of income MAX
		if requested_limit_ratio is not None and requested_limit_ratio > bnpl_max_ratio:
			hard_decline = True
			hard_decline_reason = f"BNPL limit {round(requested_limit_ratio*100)}% exceeds max 100% - Policy BNPL-001"
			policy_violations.append(PolicyViolation(
				code="BNPL-001", policy_name="BNPL Limit Policy", section="Section 4.1",
				threshold="BNPL max 100% of income", actual_value=f"{round(requested_limit_ratio*100)}%",
				severity="hard_decline"
			))
		# BNPL: Any delinquency = decline
		if delinquencies > 0 or delinquency_flags:
			hard_decline = True
			hard_decline_reason = "Previous delinquency - BNPL requires clean history - Policy BNPL-002"
			policy_violations.append(PolicyViolation(
				code="BNPL-002", policy_name="BNPL Clean History", section="Section 4.2",
				threshold="No delinquencies allowed", actual_value=f"{delinquencies} delinquencies",
				severity="hard_decline"
			))
		# BNPL: High utilization = decline
		if util_pct > 70:
			policy_violations.append(PolicyViolation(
				code="BNPL-003", policy_name="BNPL Utilization", section="Section 4.3",
				threshold="Utilization < 70%", actual_value=f"{util_pct:.0f}%",
				severity="high"
			))
	
	elif loan_type == "personal_loan":
		# Personal Loan: Income, employment, credit history requirements
		if applicant_income < 1000:
			policy_violations.append(PolicyViolation(
				code="PL-001", policy_name="Minimum Income", section="Section 5.1",
				threshold="Income >= $1000/month", actual_value=f"${applicant_income:.0f}",
				severity="high"
			))
		if emp_months < 6:
			policy_violations.append(PolicyViolation(
				code="PL-002", policy_name="Employment Stability", section="Section 5.2",
				threshold="Employment >= 6 months", actual_value=f"{emp_months} months",
				severity="medium"
			))
		if hist_months < 12:
			policy_violations.append(PolicyViolation(
				code="PL-003", policy_name="Credit History", section="Section 5.3",
				threshold="History >= 12 months", actual_value=f"{hist_months} months",
				severity="medium"
			))
		# PL limit check: Prime gets 4x, others 2x
		is_prime_pl = (dti <= 0.35 and util_pct <= 40 and delinquencies == 0 and 
					   hist_months >= 24 and emp_months >= 12 and applicant_income >= 3000)
		pl_max_ratio = 4.0 if is_prime_pl else 2.0
		if requested_limit_ratio is not None and requested_limit_ratio > pl_max_ratio:
			hard_decline = True
			hard_decline_reason = f"Limit {round(requested_limit_ratio*100)}% exceeds {round(pl_max_ratio*100)}% max for personal loan - Policy PL-005"
			policy_violations.append(PolicyViolation(
				code="PL-005", policy_name="PL Limit Policy", section="Section 5.5",
				threshold=f"Max {round(pl_max_ratio*100)}% for {'prime' if is_prime_pl else 'standard'} profile",
				actual_value=f"{round(requested_limit_ratio*100)}%",
				severity="hard_decline"
			))
	
	else:  # credit_card
		# Credit Card: History and utilization critical
		if hist_months < 6:
			policy_violations.append(PolicyViolation(
				code="CC-001", policy_name="CC History Required", section="Section 6.1",
				threshold="History >= 6 months", actual_value=f"{hist_months} months",
				severity="high"
			))
		if util_pct > 70:
			policy_violations.append(PolicyViolation(
				code="CC-002", policy_name="CC Utilization", section="Section 6.2",
				threshold="Utilization < 70%", actual_value=f"{util_pct:.0f}%",
				severity="medium"
			))
		if delinquencies > 0 and any("30" in str(f) or "60" in str(f) or "90" in str(f) for f in (delinquency_flags or [])):
			policy_violations.append(PolicyViolation(
				code="CC-003", policy_name="CC Repayment History", section="Section 6.3",
				threshold="No late payments", actual_value=f"{delinquencies} late payments",
				severity="high"
			))
		# CC limit: Prime gets 3x, others 1.5x
		is_prime_cc = (dti <= 0.40 and util_pct <= 50 and delinquencies == 0 and hist_months >= 12)
		cc_max_ratio = 3.0 if is_prime_cc else 1.5
		if requested_limit_ratio is not None and requested_limit_ratio > cc_max_ratio:
			hard_decline = True
			hard_decline_reason = f"Limit {round(requested_limit_ratio*100)}% exceeds {round(cc_max_ratio*100)}% max for credit card - Policy CC-004"
			policy_violations.append(PolicyViolation(
				code="CC-004", policy_name="CC Limit Policy", section="Section 6.4",
				threshold=f"Max {round(cc_max_ratio*100)}% for {'prime' if is_prime_cc else 'standard'} profile",
				actual_value=f"{round(requested_limit_ratio*100)}%",
				severity="hard_decline"
			))
	
	# =====================================================
	# RULE 2: DTI RATIO SCORING (Policy Section 1.1)
	# Weight: 25% of total score
	# =====================================================
	
	if dti >= 0.60:
		impact = -0.55
		score += impact
		contributors.append("DTI >= 60% (Critical - Hard Decline)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% exceeds hard limit (60%). Automatic decline.",
			severity="critical",
			policy_code="DTI-006"
		))
	elif dti >= 0.50:
		impact = -0.40
		score += impact
		contributors.append("DTI >= 50% (High Risk)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% requires senior underwriter review.",
			severity="high",
			policy_code="DTI-005"
		))
		policy_violations.append(PolicyViolation(
			code="DTI-005",
			policy_name="High DTI Policy",
			section="Section 1.1",
			threshold="DTI > 50%: Critical - Automatic decline unless exceptional",
			actual_value=f"Your DTI: {round(dti*100)}%",
			severity="violation"
		))
	elif dti >= 0.43:
		impact = -0.30
		score += impact
		contributors.append("DTI >= 43% (Elevated)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% requires additional documentation.",
			severity="high",
			policy_code="DTI-004"
		))
		policy_violations.append(PolicyViolation(
			code="DTI-004",
			policy_name="Elevated DTI Policy",
			section="Section 1.1",
			threshold="DTI 43-50%: High Risk - Requires senior underwriter review",
			actual_value=f"Your DTI: {round(dti*100)}%",
			severity="warning"
		))
	elif dti >= 0.36:
		impact = -0.20
		score += impact
		contributors.append("DTI >= 36% (Moderate)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% is in moderate risk zone.",
			severity="medium",
			policy_code="DTI-003"
		))
		policy_violations.append(PolicyViolation(
			code="DTI-003",
			policy_name="Moderate DTI Policy",
			section="Section 1.1",
			threshold="DTI 36-43%: Moderate Risk - Requires additional documentation",
			actual_value=f"Your DTI: {round(dti*100)}%",
			severity="warning"
		))
	elif dti >= 0.28:
		impact = -0.10
		score += impact
		contributors.append("DTI >= 28% (Acceptable)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% is acceptable but above ideal range.",
			severity="low",
			policy_code="DTI-002"
		))
	else:
		# DTI < 28% - Bonus
		impact = 0.05
		score += impact
		contributors.append("DTI < 28% (Excellent)")
		factor_breakdown.append(FactorContribution(
			factor_name="Debt-to-Income Ratio",
			impact=impact,
			description=f"DTI of {round(dti*100)}% is excellent. Full approval recommended.",
			severity="low",
			policy_code="DTI-001"
		))
	
	# =====================================================
	# RULE 3: DELINQUENCY SCORING (Policy Section 2.1)
	# Weight: 20% of total score
	# =====================================================
	
	# Check for severe delinquencies in flags
	has_90_plus = any("90" in f for f in delinquency_flags)
	has_60_plus = any("60" in f for f in delinquency_flags)
	has_30_plus = any("30" in f for f in delinquency_flags)
	
	if has_90_plus or delinquencies >= 3:
		impact = -0.35
		score += impact
		contributors.append("90+ days past due or 3+ delinquencies (Serious)")
		factor_breakdown.append(FactorContribution(
			factor_name="Payment History",
			impact=impact,
			description="Serious delinquency: 90+ days past due detected.",
			severity="critical",
			policy_code="DEL-003"
		))
		policy_violations.append(PolicyViolation(
			code="DEL-003",
			policy_name="Serious Delinquency Policy",
			section="Section 2.1",
			threshold="90+ Days Past Due (DPD-90): Serious delinquency, -35 points",
			actual_value=f"Delinquencies: {delinquency_flags}",
			severity="violation"
		))
	elif has_60_plus or delinquencies == 2:
		impact = -0.20
		score += impact
		contributors.append("60+ days past due (Moderate)")
		factor_breakdown.append(FactorContribution(
			factor_name="Payment History",
			impact=impact,
			description="Moderate delinquency: 60+ days past due detected.",
			severity="high",
			policy_code="DEL-002"
		))
		policy_violations.append(PolicyViolation(
			code="DEL-002",
			policy_name="Moderate Delinquency Policy",
			section="Section 2.1",
			threshold="60 Days Past Due (DPD-60): Moderate delinquency, -20 points",
			actual_value=f"Delinquencies: {delinquency_flags}",
			severity="warning"
		))
	elif has_30_plus or delinquencies == 1:
		impact = -0.10
		score += impact
		contributors.append("30+ days past due (Minor)")
		factor_breakdown.append(FactorContribution(
			factor_name="Payment History",
			impact=impact,
			description="Minor delinquency: 30+ days past due detected.",
			severity="medium",
			policy_code="DEL-001"
		))
		policy_violations.append(PolicyViolation(
			code="DEL-001",
			policy_name="Minor Delinquency Policy",
			section="Section 2.1",
			threshold="30 Days Past Due (DPD-30): Minor delinquency, -10 points",
			actual_value=f"Delinquencies: {delinquency_flags}",
			severity="info"
		))
	else:
		# Clean payment history - Bonus
		impact = 0.05
		score += impact
		contributors.append("Clean payment history (Excellent)")
		factor_breakdown.append(FactorContribution(
			factor_name="Payment History",
			impact=impact,
			description="No delinquencies on record. Excellent payment behavior.",
			severity="low"
		))
	
	# =====================================================
	# RULE 4: REQUESTED LIMIT RATIO (Policy Section 3.3)
	# Weight: 10% of total score
	# =====================================================
	
	if requested_limit_ratio is not None:
		if requested_limit_ratio > 2.0:
			impact = -0.25
			score += impact
			contributors.append("Requested limit > 200% of income (Decline)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Request Amount",
				impact=impact,
				description=f"Requesting {round(requested_limit_ratio*100)}% of income - excessive.",
				severity="critical",
				policy_code="REQ-003"
			))
			policy_violations.append(PolicyViolation(
				code="REQ-003",
				policy_name="Excessive Request Policy",
				section="Section 3.3",
				threshold="Ratio > 200%: Decline - unrealistic request",
				actual_value=f"Requested: {round(requested_limit_ratio*100)}% of income",
				severity="violation"
			))
		elif requested_limit_ratio > 1.0:
			impact = -0.15
			score += impact
			contributors.append("Requested limit > 100% of income (Flag)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Request Amount",
				impact=impact,
				description=f"Requesting {round(requested_limit_ratio*100)}% of income - automatic flag.",
				severity="high",
				policy_code="REQ-002"
			))
			policy_violations.append(PolicyViolation(
				code="REQ-002",
				policy_name="High Request Policy",
				section="Section 3.3",
				threshold="Ratio > 100%: Excessive - automatic flag for review",
				actual_value=f"Requested: {round(requested_limit_ratio*100)}% of income",
				severity="warning"
			))
		elif requested_limit_ratio > 0.50:
			impact = -0.10
			score += impact
			contributors.append("Requested limit > 50% of income")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Request Amount",
				impact=impact,
				description=f"Requesting {round(requested_limit_ratio*100)}% of income - requires justification.",
				severity="medium",
				policy_code="REQ-001"
			))
		elif requested_limit_ratio <= 0.25:
			impact = 0.05
			score += impact
			contributors.append("Conservative credit request (≤25% of income)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Request Amount",
				impact=impact,
				description=f"Conservative request ({round(requested_limit_ratio*100)}% of income) - auto-approve eligible.",
				severity="low"
			))
	
	# =====================================================
	# RULE 5: CREDIT UTILIZATION (Policy Section 2.2)
	# Weight: 10% of total score
	# =====================================================
	
	if credit_utilization is not None:
		# Normalize utilization to percentage (0-100)
		util_pct = credit_utilization * 100 if credit_utilization <= 1.0 else credit_utilization
		
		if util_pct > 90:
			impact = -0.25
			score += impact
			contributors.append("Credit utilization > 90% (Critical)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Utilization",
				impact=impact,
				description=f"Utilization at {round(util_pct)}% - strong decline indicator.",
				severity="critical",
				policy_code="UTL-005"
			))
			policy_violations.append(PolicyViolation(
				code="UTL-005",
				policy_name="Critical Utilization Policy",
				section="Section 2.2",
				threshold="Utilization > 90%: Critical - strong decline indicator",
				actual_value=f"Your utilization: {round(util_pct)}%",
				severity="violation"
			))
		elif util_pct > 75:
			impact = -0.15
			score += impact
			contributors.append("Credit utilization > 75% (High)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Utilization",
				impact=impact,
				description=f"Utilization at {round(util_pct)}% suggests credit stress.",
				severity="high",
				policy_code="UTL-004"
			))
		elif util_pct > 50:
			impact = -0.08
			score += impact
			contributors.append("Credit utilization > 50%")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Utilization",
				impact=impact,
				description=f"Utilization at {round(util_pct)}% may indicate cash flow issues.",
				severity="medium",
				policy_code="UTL-003"
			))
		elif util_pct <= 30:
			impact = 0.05
			score += impact
			contributors.append("Credit utilization ≤ 30% (Excellent)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit Utilization",
				impact=impact,
				description=f"Excellent utilization at {round(util_pct)}%.",
				severity="low"
			))
	
	# =====================================================
	# RULE 6: MINIMUM INCOME CHECK (Policy Section 1.3)
	# =====================================================
	
	if income is not None:
		min_income = 3000  # USD monthly minimum
		if income < min_income:
			impact = -0.15
			score += impact
			contributors.append("Below minimum income requirement")
			factor_breakdown.append(FactorContribution(
				factor_name="Income Level",
				impact=impact,
				description=f"Income ${income:,.0f} is below minimum ${min_income:,}.",
				severity="high",
				policy_code="INC-001"
			))
			policy_violations.append(PolicyViolation(
				code="INC-001",
				policy_name="Minimum Income Policy",
				section="Section 1.3",
				threshold=f"Minimum income: ${min_income:,}/month",
				actual_value=f"Your income: ${income:,.0f}/month",
				severity="violation"
			))
	
	# =====================================================
	# RULE 7: CREDIT HISTORY LENGTH (Policy Section 2.3)
	# =====================================================
	
	if credit_history_months is not None:
		if credit_history_months < 6:
			impact = -0.15
			score += impact
			contributors.append("Thin credit file (< 6 months)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit History Length",
				impact=impact,
				description="Limited credit data for decision (thin file).",
				severity="high",
				policy_code="HIST-001"
			))
			policy_violations.append(PolicyViolation(
				code="HIST-001",
				policy_name="Thin File Policy",
				section="Section 2.3",
				threshold="< 6 months: Thin file - limited data for decision",
				actual_value=f"Credit history: {credit_history_months} months",
				severity="warning"
			))
		elif credit_history_months < 12:
			impact = -0.08
			score += impact
			contributors.append("New credit user (6-12 months)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit History Length",
				impact=impact,
				description="New credit user - higher scrutiny applied.",
				severity="medium"
			))
		elif credit_history_months >= 84:  # 7+ years
			impact = 0.05
			score += impact
			contributors.append("Mature credit history (7+ years)")
			factor_breakdown.append(FactorContribution(
				factor_name="Credit History Length",
				impact=impact,
				description=f"Mature credit history of {credit_history_months//12} years - most favorable.",
				severity="low"
			))
	
	# =====================================================
	# RULE 8: EMPLOYMENT STABILITY (Policy Section 4.1)
	# =====================================================
	
	if employment_months is not None:
		if employment_months < 6:
			impact = -0.12
			score += impact
			contributors.append("Employment < 6 months")
			factor_breakdown.append(FactorContribution(
				factor_name="Employment Stability",
				impact=impact,
				description="Less than 6 months in current role - insufficient tenure.",
				severity="high",
				policy_code="EMP-001"
			))
			policy_violations.append(PolicyViolation(
				code="EMP-001",
				policy_name="Employment Tenure Policy",
				section="Section 4.1",
				threshold="Minimum 6 months in current role required",
				actual_value=f"Current tenure: {employment_months} months",
				severity="warning"
			))
		elif employment_months >= 60:  # 5+ years
			impact = 0.05
			score += impact
			contributors.append("Long-term employment (5+ years)")
			factor_breakdown.append(FactorContribution(
				factor_name="Employment Stability",
				impact=impact,
				description=f"Strong employment stability - {employment_months//12} years with employer.",
				severity="low"
			))

	# =====================================================
	# RULE 9: AGE POLICY (Policy Section 5.1)
	# =====================================================
	if age is not None:
		if age < 21:
			impact = -0.10
			score += impact
			contributors.append("Young applicant (< 21 years)")
			factor_breakdown.append(FactorContribution(
				factor_name="Age Factor",
				impact=impact,
				description="Applicant under 21 - requires co-signer per Policy AGE-001.",
				severity="medium",
				policy_code="AGE-001"
			))
		elif age > 65:
			impact = -0.05
			score += impact
			contributors.append("Senior applicant (> 65 years)")
			factor_breakdown.append(FactorContribution(
				factor_name="Age Factor",
				impact=impact,
				description="Applicant over 65 - requires retirement income verification.",
				severity="low",
				policy_code="AGE-002"
			))
	
	# =====================================================
	# FINAL SCORE CALCULATION
	# =====================================================
	
	# Ensure score is within bounds
	score = max(0.0, min(1.0, score))
	
	# Determine band
	if hard_decline:
		band = "decline"
	elif score >= 0.75:
		band = "excellent"
	elif score >= 0.60:
		band = "good"
	elif score >= 0.45:
		band = "medium"
	else:
		band = "low"
	
	return ScorecardResult(
		score=score,
		band=band,
		contributors=contributors,
		factor_breakdown=factor_breakdown,
		policy_violations=policy_violations,
		base_score=base_score,
		hard_decline=hard_decline,
		hard_decline_reason=hard_decline_reason,
	)


def simulate_what_if(
	*, 
	current_income: float, 
	current_liabilities: float,
	current_delinquencies: int,
	requested_limit: float | None,
	# What-if parameters
	liability_reduction: float = 0,
	income_increase: float = 0,
	delinquency_flags: list[str] | None = None,
) -> dict:
	"""
	Simulate how changes in financial situation would affect the credit decision.
	All calculations done by Python - no LLM math involved.
	"""
	delinquency_flags = delinquency_flags or []
	
	# Current scenario
	current_dti = current_liabilities / current_income if current_income > 0 else 1.0
	current_result = calculate_scorecard(
		dti=current_dti,
		delinquencies=current_delinquencies,
		requested_limit_ratio=(requested_limit / current_income) if (requested_limit and current_income > 0) else None,
		delinquency_flags=delinquency_flags,
	)
	
	# Simulated scenario
	new_liabilities = max(0, current_liabilities - liability_reduction)
	new_income = current_income + income_increase
	new_dti = new_liabilities / new_income if new_income > 0 else 1.0
	simulated_result = calculate_scorecard(
		dti=new_dti,
		delinquencies=current_delinquencies,  # Delinquencies don't change in simulation
		requested_limit_ratio=(requested_limit / new_income) if (requested_limit and new_income > 0) else None,
		delinquency_flags=delinquency_flags,
	)
	
	# Calculate improvement
	score_improvement = simulated_result.score - current_result.score
	
	# Determine decisions
	def get_decision(score: float, hard_decline: bool) -> str:
		if hard_decline:
			return "decline"
		return "approve" if score >= 0.75 else ("review" if score >= 0.50 else "decline")
	
	decision_current = get_decision(current_result.score, current_result.hard_decline)
	decision_simulated = get_decision(simulated_result.score, simulated_result.hard_decline)
	
	return {
		"current": {
			"score": round(current_result.score * 100),
			"dti": round(current_dti * 100, 1),
			"decision": decision_current,
			"band": current_result.band
		},
		"simulated": {
			"score": round(simulated_result.score * 100),
			"dti": round(new_dti * 100, 1),
			"decision": decision_simulated,
			"band": simulated_result.band
		},
		"improvement": {
			"score_change": round(score_improvement * 100),
			"dti_change": round((current_dti - new_dti) * 100, 1),
			"decision_improved": decision_simulated != decision_current and (
				(decision_current == "decline" and decision_simulated in ["review", "approve"]) or
				(decision_current == "review" and decision_simulated == "approve")
			)
		}
	}
