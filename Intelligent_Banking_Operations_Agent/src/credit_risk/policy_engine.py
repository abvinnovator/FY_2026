from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyDecision:
	override: bool
	reason: str | None = None


def apply_minimums(*, score: float, dti: float) -> PolicyDecision:
	"""Simple policy gating: minimum score and max DTI."""
	if score < 0.45:
		return PolicyDecision(override=True, reason="score below policy minimum")
	if dti > 0.6:
		return PolicyDecision(override=True, reason="DTI above allowed maximum")
	return PolicyDecision(override=False)


