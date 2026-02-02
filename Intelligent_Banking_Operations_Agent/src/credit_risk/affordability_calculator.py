from __future__ import annotations


def compute_dti(income: float, liabilities: float) -> float:
	if income <= 0:
		return 1.0
	return liabilities / income



