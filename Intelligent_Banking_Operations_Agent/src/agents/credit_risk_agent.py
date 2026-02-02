from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.credit_risk.affordability_calculator import compute_dti
from src.credit_risk.scorecard import calculate_scorecard, simulate_what_if, PolicyViolation
from src.credit_risk.policy_engine import apply_minimums
from src.credit_risk.fuzzy_scorecard import calculate_fuzzy_score, FuzzyScorecardResult
from src.credit_risk.catboost_model import predict_credit_risk, MLPredictionResult


@dataclass
class CreditTriageOutput:
	score: float
	decision: str
	rationale: str
	policy_citations: list[str]
	key_factors: list[str]
	# Novel fields
	factor_breakdown: list[dict] = field(default_factory=list)
	improvement_tips: list[str] = field(default_factory=list)
	what_if_scenarios: list[dict] = field(default_factory=list)
	risk_summary: dict = field(default_factory=dict)
	# NEW: Policy Violations
	policy_violations: list[dict] = field(default_factory=list)
	hard_decline: bool = False
	hard_decline_reason: str | None = None
	# NEW: Fuzzy Logic Results
	fuzzy_score: float | None = None
	fuzzy_rules_fired: list[dict] = field(default_factory=list)
	fuzzy_dominant_rules: list[str] = field(default_factory=list)
	scoring_method: str = "fuzzy"  # 'fuzzy' or 'traditional'


class CreditRiskAgent:
	"""
	Enhanced Credit Risk Agent with Novel Features:
	1. FUZZY LOGIC SCORING with 10 rules (Mamdani Inference)
	2. Factor Contribution Analysis (Explainable AI)
	3. What-If Scenario Simulation
	4. AI-Powered Improvement Recommendations
	5. Policy Violation Tracking with Codes
	
	FUZZY LOGIC RULES (10 rules based on RBI/Basel III/OCC):
	- FUZZY-DTI-001: DTI Excellence Rule
	- FUZZY-DTI-002: High DTI Risk Rule
	- FUZZY-DTI-003: Critical DTI Rule
	- FUZZY-DEL-001: Clean Payment History Rule
	- FUZZY-DEL-002: Serious Delinquency Rule
	- FUZZY-EMP-001: Employment Stability Rule
	- FUZZY-HIST-001: Thin Credit File Rule
	- FUZZY-REQ-001: Conservative Request Rule
	- FUZZY-REQ-002: Excessive Request Rule
	- FUZZY-BALANCED-001: Balanced Profile Rule
	
	ARCHITECTURE (per CFA Institute RAG Research):
	- Fuzzy inference with triangular/trapezoidal membership functions
	- ALL calculations done by Python (deterministic, accurate)
	- LLM only receives pre-calculated values and writes human-readable text
	- LLM cites specific policy violations with codes
	"""

	def triage(
		self, 
		*, 
		income: float, 
		liabilities: float, 
		delinquency_flags: list[str] | None, 
		requested_limit: float | None,
		# New optional parameters for enhanced analysis
		credit_utilization: float | None = None,
		employment_months: int | None = None,
		credit_history_months: int | None = None,
		age: int | None = None,
		loan_type: str = "bnpl",
	) -> CreditTriageOutput:
		# ========================================
		# STEP 1: ALL CALCULATIONS DONE IN PYTHON
		# Using FUZZY LOGIC with 10 rules
		# ========================================
		
		dti = compute_dti(income, liabilities)
		delinquencies = len(delinquency_flags or [])
		requested_limit_ratio = (requested_limit / income) if (requested_limit and income > 0) else None
		
		# ==========================================
		# FUZZY LOGIC SCORING (10 RULES)
		# Uses Mamdani fuzzy inference system
		# ==========================================
		print("\n" + "="*80)
		print("🚀 [AGENT] FUZZY LOGIC TRIGGERED")
		print("="*80)
		print(f"📥 Inputs: DTI={dti*100:.1f}%, Utilization={credit_utilization or 30.0}%, Delinquencies={delinquencies}")
		
		fuzzy_result = calculate_fuzzy_score(
			dti=dti,
			delinquencies=delinquencies,
			requested_limit_ratio=requested_limit_ratio,
			delinquency_flags=delinquency_flags,
			credit_utilization=credit_utilization,
			employment_months=employment_months,
			credit_history_months=credit_history_months,
			age=age,
			income=income,
			loan_type=loan_type,
		)
		
		print(f"✅ FUZZY COMPLETE: Score={fuzzy_result.score}, Decision={fuzzy_result.decision}, Band={fuzzy_result.band}")
		print(f"📜 Rules Fired: {len([r for r in fuzzy_result.rule_results if r.firing_strength > 0])} rules")
		for r in fuzzy_result.dominant_rules[:3]:
			print(f"   - {r}")
		
		# ==========================================
		# ML LOGIC (CATBOOST MODEL)
		# Production ML model for default prediction
		# ==========================================
		print("\n" + "="*80)
		print("🧠 [AGENT] ML LOGIC TRIGGERED (CatBoost)")
		print("="*80)
		
		# Map inputs for ML model
		# ML Model features (per notebook): 
		# 1. dti (decimal)
		# 2. utilization (decimal) 
		# 3. limit_ratio (decimal)
		# 4. delinquency (max delay level 0-6)
		# 5. credit_history (count of months with delay 0-6)
		
		ml_utilization = (credit_utilization / 100.0) if (credit_utilization and credit_utilization > 1.0) else (credit_utilization or 0.3)
		
		# For delinquency/history, we map the flags if available
		ml_delinquency = 0
		ml_credit_history_count = 0
		
		if delinquency_flags:
			ml_credit_history_count = min(6, len(delinquency_flags))
			flag_str = " ".join(delinquency_flags).lower()
			if "90" in flag_str: ml_delinquency = 4
			elif "60" in flag_str: ml_delinquency = 3
			elif "30" in flag_str: ml_delinquency = 2
		elif delinquencies > 0:
			ml_delinquency = 2
			ml_credit_history_count = min(6, delinquencies)
		
		print(f"📥 ML Inputs: dti={dti:.4f}, utilization={ml_utilization:.4f}, limit_ratio={requested_limit_ratio or 0.4:.4f}")
		print("⏳ Processing through CatBoost model...")
		
		try:
			ml_result = predict_credit_risk(
				dti=dti,
				utilization=ml_utilization,
				limit_ratio=requested_limit_ratio or 0.4,
				delinquency=ml_delinquency,
				credit_history=ml_credit_history_count
			)
			print(f"✅ ML OUTPUT: Probability of Default={ml_result.default_probability*100:.1f}%")
			print(f"📈 Risk Level: {ml_result.risk_level}")
			print(f"🚩 Top Factors: {ml_result.top_risk_factors}")
		except Exception as e:
			print(f"❌ ML MODEL ERROR: {e}")
			ml_result = None
		
		# Also run traditional scorecard for comparison (keeps existing policy violations)
		sc = calculate_scorecard(
			dti=dti, 
			delinquencies=delinquencies, 
			requested_limit_ratio=requested_limit_ratio,
			delinquency_flags=delinquency_flags,
			credit_utilization=credit_utilization,
			employment_months=employment_months,
			credit_history_months=credit_history_months,
			age=age,
			income=income,
			loan_type=loan_type,
		)
		
		policy = apply_minimums(score=sc.score, dti=dti)
		
		# ==========================================
		# USE FUZZY SCORE FOR DECISION
		# Fuzzy score is 0-100, convert to decision
		# ==========================================
		fuzzy_score_normalized = fuzzy_result.score / 100.0  # Convert to 0-1 scale
		
		# Check for hard declines (from policy violations)
		has_hard_decline = bool(fuzzy_result.policy_violations) or sc.hard_decline
		
		if has_hard_decline:
			decision = "decline"
		elif fuzzy_result.decision == "approve":
			decision = "approve"
		elif fuzzy_result.decision == "review":
			decision = "review"
		else:
			decision = "decline"
		
		if policy.override and decision == "approve":
			decision = "review"
		
		key_factors = sc.contributors or ["no adverse factors"]
		if policy.override and policy.reason:
			key_factors.append(policy.reason)
		
		# Add fuzzy rule insights to key factors
		for dominant_rule in fuzzy_result.dominant_rules[:2]:
			key_factors.append(f"Fuzzy: {dominant_rule}")

		# === PRE-CALCULATE: Factor Contribution Breakdown ===
		factor_breakdown = []
		for fc in sc.factor_breakdown:
			factor_breakdown.append({
				"name": fc.factor_name,
				"impact": round(fc.impact * 100),
				"description": fc.description,
				"severity": fc.severity,
				"policy_code": fc.policy_code,
			})

		# === PRE-CALCULATE: Policy Violations ===
		policy_violations = []
		for pv in sc.policy_violations:
			policy_violations.append({
				"code": pv.code,
				"policy_name": pv.policy_name,
				"section": pv.section,
				"threshold": pv.threshold,
				"actual_value": pv.actual_value,
				"severity": pv.severity,
			})

		# === PRE-CALCULATE: What-If Scenarios ===
		what_if_scenarios = []
		
		debt_reduction_20_pct = round(liabilities * 0.2, 2)
		debt_reduction_50_pct = round(liabilities * 0.5, 2)
		conservative_limit = round(income * 0.25, 2) if income > 0 else 0
		
		if liabilities > 0:
			scenario1 = simulate_what_if(
				current_income=income,
				current_liabilities=liabilities,
				current_delinquencies=delinquencies,
				requested_limit=requested_limit,
				liability_reduction=debt_reduction_20_pct,
				delinquency_flags=delinquency_flags,
			)
			what_if_scenarios.append({
				"name": "Pay off 20% of debt",
				"action": f"Reduce liabilities by ${debt_reduction_20_pct:,.2f}",
				**scenario1
			})
			
			scenario2 = simulate_what_if(
				current_income=income,
				current_liabilities=liabilities,
				current_delinquencies=delinquencies,
				requested_limit=requested_limit,
				liability_reduction=debt_reduction_50_pct,
				delinquency_flags=delinquency_flags,
			)
			what_if_scenarios.append({
				"name": "Pay off 50% of debt",
				"action": f"Reduce liabilities by ${debt_reduction_50_pct:,.2f}",
				**scenario2
			})

		if requested_limit and requested_limit_ratio and requested_limit_ratio > 0.3:
			scenario3 = simulate_what_if(
				current_income=income,
				current_liabilities=liabilities,
				current_delinquencies=delinquencies,
				requested_limit=conservative_limit,
				liability_reduction=0,
				delinquency_flags=delinquency_flags,
			)
			what_if_scenarios.append({
				"name": "Request conservative limit",
				"action": f"Request ${conservative_limit:,.2f} instead of ${requested_limit:,.2f}",
				**scenario3
			})

		# === PRE-CALCULATE: Risk Summary (Using Fuzzy Score) ===
		risk_summary = {
			"overall_score": round(fuzzy_result.score),  # Use fuzzy score
			"traditional_score": round(sc.score * 100),   # Keep traditional for comparison
			"base_score": 100,
			"total_deductions": round(100 - fuzzy_result.score),
			"risk_level": fuzzy_result.band,
			"dti_percent": round(dti * 100, 1),
			"factors_analyzed": len(sc.factor_breakdown),
			"critical_factors": sum(1 for f in sc.factor_breakdown if f.severity == "critical"),
			"high_factors": sum(1 for f in sc.factor_breakdown if f.severity == "high"),
			"violations_count": len(policy_violations),
			"hard_decline": has_hard_decline,
			# Fuzzy Logic Details
			"scoring_method": "fuzzy_logic",
			"fuzzy_rules_count": 10,
			"fuzzy_rules_fired": len([r for r in fuzzy_result.rule_results if r.firing_strength > 0]),
			"dominant_fuzzy_rules": fuzzy_result.dominant_rules[:3],
		}

		# === PRE-CALCULATE: Improvement Tips ===
		improvement_tips_calculated = []
		
		if dti >= 0.35:
			target_dti = 0.30
			current_payment = liabilities
			target_payment = income * target_dti
			reduction_needed = current_payment - target_payment
			if reduction_needed > 0:
				improvement_tips_calculated.append({
					"tip": f"Reduce monthly debt payments by ${reduction_needed:,.2f} to achieve a healthier 30% DTI ratio.",
					"impact": "Could improve score by ~25 points",
					"policy_ref": "Section 1.1 - DTI Policy"
				})
		
		if delinquencies > 0:
			improvement_tips_calculated.append({
				"tip": "Maintain on-time payments for at least 6 consecutive months to demonstrate payment reliability.",
				"impact": f"Could improve score by ~{delinquencies * 15} points",
				"policy_ref": "Section 2.1 - Payment History"
			})
		
		if requested_limit_ratio and requested_limit_ratio > 0.5:
			improvement_tips_calculated.append({
				"tip": f"Consider requesting ${conservative_limit:,.2f} (25% of income) instead of ${requested_limit:,.2f}.",
				"impact": "Could improve score by ~15-20 points",
				"policy_ref": "Section 3.3 - Request Limit Policy"
			})
		
		if not improvement_tips_calculated and sc.score < 0.75:
			improvement_tips_calculated.append({
				"tip": "Build a longer credit history by keeping accounts open and active.",
				"impact": "Gradual improvement over 6-12 months",
				"policy_ref": "Section 2.3 - Credit History"
			})

		# ========================================
		# STEP 2: LLM ONLY WRITES TEXT (NO CALCULATIONS)
		# All numbers are PRE-CALCULATED by Python above
		# LLM MUST cite policy violations
		# ========================================
		
		# ========================================
		# STEP 2: LLM TRIGGERED (GENERATE RATIONALE)
		# LLM receives pre-calculated values
		# ========================================
		from src.core.config import get_settings
		settings = get_settings()
		
		print("\n" + "="*80)
		print("🤖 [AGENT] LLM TRIGGERED (Gemini-2.0)")
		print("="*80)
		print("⏳ Generating human-readable rationale citing policies...")
		
		rationale = ""
		
		if settings.google_api_key and settings.google_api_key not in ["your_google_api_key_here", ""]:
			try:
				import google.generativeai as genai
				genai.configure(api_key=settings.google_api_key)
				model = genai.GenerativeModel('gemini-2.5-flash')
				
				# Build factor summary with PRE-CALCULATED values
				factor_summary = "\n".join([
					f"  - {f['name']}: {f['impact']:+d} points ({f['severity']} severity)" 
					+ (f" [Policy {f['policy_code']}]" if f.get('policy_code') else "")
					for f in factor_breakdown
				])
				
				# Build policy violations summary
				violations_summary = ""
				if policy_violations:
					violations_summary = "=== POLICY VIOLATIONS DETECTED ===\n"
					for pv in policy_violations:
						violations_summary += f"  - [{pv['code']}] {pv['policy_name']} ({pv['section']})\n"
						violations_summary += f"    Threshold: {pv['threshold']}\n"
						violations_summary += f"    Actual: {pv['actual_value']}\n"
						violations_summary += f"    Severity: {pv['severity'].upper()}\n\n"
				else:
					violations_summary = "=== NO POLICY VIOLATIONS DETECTED ===\nApplication meets all policy requirements.\n"
				
				# Build improvement tips summary
				tips_summary = "\n".join([
					f"  - {t['tip']} (Ref: {t['policy_ref']})" 
					for t in improvement_tips_calculated
				])
				
				requested_limit_str = f"${requested_limit:,.2f}" if requested_limit else "$0"
				
				# CRITICAL: Prompt tells LLM to cite specific policies
				prompt = f"""You are a Senior Credit Underwriter at a major bank. Your task is to write a professional rationale that cites specific policies.

IMPORTANT: 
1. Use ONLY the exact numbers provided below - do NOT calculate any new numbers
2. You MUST cite the specific policy codes (like DTI-003, DEL-001) when explaining the decision
3. Reference the exact policy thresholds that were violated or met

=== PRE-CALCULATED APPLICATION DATA ===
- Final Decision: {decision.upper()}
- Credit Score: {round(sc.score * 100)}/100
- DTI Ratio: {round(dti * 100, 1)}% (${liabilities:,.2f} liabilities ÷ ${income:,.2f} income)
- Number of Delinquencies: {delinquencies}
- Requested Credit Limit: {requested_limit_str}
- Hard Decline: {"YES - " + (sc.hard_decline_reason or "") if sc.hard_decline else "NO"}

=== PRE-CALCULATED FACTOR BREAKDOWN ===
{factor_summary}

{violations_summary}

=== IMPROVEMENT RECOMMENDATIONS ===
{tips_summary if tips_summary else "No specific improvements needed."}

=== YOUR TASK ===
Write a 3-4 sentence professional rationale that:
1. States the decision clearly
2. Cites the SPECIFIC policy codes that were violated (e.g., "Per Policy DTI-003...")
3. References the exact thresholds from the policy document
4. Mentions one actionable improvement if the decision is not "approve"

Respond with ONLY the rationale text. Be professional and empathetic."""
				
				response = model.generate_content(prompt)
				rationale = response.text.strip()
				print(f"✅ LLM COMPLETE: Rationale generated ({len(rationale)} chars)")
				print("="*80 + "\n")
				
			except Exception as e:
				import traceback
				traceback.print_exc()
				rationale = f"Error generating AI rationale: {str(e)}. Check console for details."
		else:
			# Build a basic rationale without AI
			rationale = self._build_basic_rationale(decision, dti, delinquencies, policy_violations, sc.hard_decline)

		# Extract policy citations from violations
		policy_citations = [f"[{pv['code']}] {pv['policy_name']}" for pv in policy_violations]

		final_improvement_tips = [t["tip"] for t in improvement_tips_calculated]

		# Prepare fuzzy rules for output
		fuzzy_rules_fired = [
			{
				"rule_id": r.rule_id,
				"rule_name": r.rule_name,
				"firing_strength": r.firing_strength,
				"policy_reference": r.policy_reference,
			}
			for r in fuzzy_result.rule_results if r.firing_strength > 0
		]

		return CreditTriageOutput(
			score=fuzzy_score_normalized,  # Use fuzzy score (normalized 0-1)
			decision=decision,
			rationale=rationale,
			policy_citations=policy_citations,
			key_factors=key_factors,
			factor_breakdown=factor_breakdown,
			improvement_tips=final_improvement_tips[:3],
			what_if_scenarios=what_if_scenarios,
			risk_summary=risk_summary,
			policy_violations=policy_violations,
			hard_decline=has_hard_decline,
			hard_decline_reason=sc.hard_decline_reason if sc.hard_decline else (
				fuzzy_result.policy_violations[0] if fuzzy_result.policy_violations else None
			),
			# Fuzzy Logic Results
			fuzzy_score=fuzzy_result.score,
			fuzzy_rules_fired=fuzzy_rules_fired,
			fuzzy_dominant_rules=fuzzy_result.dominant_rules,
			scoring_method="fuzzy",
		)
	
	def _build_basic_rationale(
		self, 
		decision: str, 
		dti: float, 
		delinquencies: int, 
		policy_violations: list[dict],
		hard_decline: bool
	) -> str:
		"""Build a basic rationale without AI when API key is not available."""
		if hard_decline:
			pv = policy_violations[0] if policy_violations else {}
			return (
				f"Application DECLINED per {pv.get('code', 'bank policy')}. "
				f"{pv.get('threshold', 'Policy requirements not met.')} "
				f"This is a hard decline and cannot be overridden at branch level."
			)
		
		if decision == "approve":
			return (
				f"Application APPROVED. DTI of {round(dti*100)}% meets policy requirements. "
				f"Payment history is satisfactory. Please proceed with standard disbursement process."
			)
		
		violation_codes = ", ".join([pv['code'] for pv in policy_violations[:3]]) if policy_violations else "multiple factors"
		
		if decision == "review":
			return (
				f"Application flagged for REVIEW. Policy violations detected: {violation_codes}. "
				f"DTI of {round(dti*100)}% and {delinquencies} delinquencies require senior underwriter assessment."
			)
		
		return (
			f"Application DECLINED. Policy violations: {violation_codes}. "
			f"DTI of {round(dti*100)}% exceeds acceptable thresholds. "
			f"Recommend applicant reduce debt obligations before reapplying."
		)
