from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.credit_risk.affordability_calculator import compute_dti
from src.credit_risk.scorecard import calculate_scorecard
from src.credit_risk.policy_engine import apply_minimums

@dataclass
class CreditTriageOutput:
	score: float
	decision: str
	rationale: str
	policy_citations: list[str]
	key_factors: list[str]


class CreditRiskAgent:
	"""Simple scorecard-like credit triage.

	This is a minimal placeholder; full logic will be in credit_risk modules.
	"""

	def triage(self, *, income: float, liabilities: float, delinquency_flags: list[str] | None, requested_limit: float | None) -> CreditTriageOutput:
		dti = compute_dti(income, liabilities)
		delinquencies = len(delinquency_flags or [])
		requested_limit_ratio = (requested_limit / income) if (requested_limit and income > 0) else None
		sc = calculate_scorecard(dti=dti, delinquencies=delinquencies, requested_limit_ratio=requested_limit_ratio)
		policy = apply_minimums(score=sc.score, dti=dti)
		decision = "approve" if sc.score >= 0.75 else ("review" if sc.score >= 0.5 else "decline")
		if policy.override and decision == "approve":
			decision = "review"
		
		key_factors = sc.contributors or ["no adverse factors"]
		if policy.override and policy.reason:
			key_factors.append(policy.reason)

		# --- Gemini Logic Start ---
		from src.core.config import get_settings
		settings = get_settings()
		
		rationale = ""
		if settings.google_api_key and settings.google_api_key not in ["your_google_api_key_here", ""]:
			try:
				import google.generativeai as genai
				genai.configure(api_key=settings.google_api_key)
				model = genai.GenerativeModel('gemini-2.5-flash')
				
				prompt = (
					f"You are a Senior Underwriter. A credit application has been processed:\n"
					f"- Decision: {decision}\n"
					f"- Score: {round(sc.score * 100)}/100\n"
					f"- DTI Ratio: {round(dti, 2)}\n"
					f"- Key Factors: {', '.join(key_factors)}\n\n"
					"Based on these factors, write a professional 2-sentence rationale for the client."
				)
				
				response = model.generate_content(prompt)
				rationale = response.text
			except Exception as e:
				import traceback
				traceback.print_exc()
				rationale = f"Error generating AI rationale: {str(e)}. Check console for details."
		else:
			rationale = "AI Reasoning Service is currently disabled. Please provide a GOOGLE_API_KEY in .env."
		# --- Gemini Logic End ---

		return CreditTriageOutput(
			score=sc.score,
			decision=decision,
			rationale=rationale,
			policy_citations=[],
			key_factors=key_factors,
		)


