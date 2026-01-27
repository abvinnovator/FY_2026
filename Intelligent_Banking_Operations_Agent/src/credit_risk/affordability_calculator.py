from __future__ import annotations


def compute_dti(income: float, liabilities: float) -> float:
	if income <= 0:
		return 1.0
	return liabilities / income


def stress_test_payment(interest_rate: float, term_months: int, principal: float) -> float:
	"""Simplified monthly payment stress test using fixed rate formula.

	This is a placeholder; for cards it's less relevant, but useful for demo.
	"""
	r = interest_rate / 12.0
	n = max(1, term_months)
	if r == 0:
		return principal / n
	return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


