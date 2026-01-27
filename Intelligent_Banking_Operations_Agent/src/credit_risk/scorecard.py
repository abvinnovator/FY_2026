from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScorecardResult:
	score: float
	band: str
	contributors: list[str]


def calculate_scorecard(*, dti: float, delinquencies: int, requested_limit_ratio: float | None) -> ScorecardResult:
	score = 1.0
	contributors: list[str] = []
	if dti >= 0.5:
		score -= 0.45
		contributors.append("DTI >= 50%")
	elif dti >= 0.35:
		score -= 0.25
		contributors.append("DTI >= 35%")

	if delinquencies >= 2:
		score -= 0.35
		contributors.append("2+ delinquencies")
	elif delinquencies == 1:
		score -= 0.2
		contributors.append("1 delinquency")

	if requested_limit_ratio is not None and requested_limit_ratio > 0.5:
		score -= 0.2
		contributors.append("requested limit > 50% of income")

	score = max(0.0, min(1.0, score))
	band = "high" if score >= 0.75 else ("medium" if score >= 0.5 else "low")
	return ScorecardResult(score=score, band=band, contributors=contributors)


