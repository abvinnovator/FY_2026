from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Intent = Literal["fraud", "credit", "operations"]


@dataclass
class RoutingDecision:
	intent: Intent
	guardrails_ok: bool


class BankingSupervisor:
	"""Supervisor agent for intent classification and guardrails.

	Minimal deterministic classifier based on presence of transaction vs application fields.
	"""

	def classify(self, payload: dict) -> RoutingDecision:
		if {"account_id", "amount"}.issubset(payload.keys()):
			return RoutingDecision(intent="fraud", guardrails_ok=True)
		if {"income", "liabilities"}.issubset(payload.keys()):
			return RoutingDecision(intent="credit", guardrails_ok=True)
		return RoutingDecision(intent="operations", guardrails_ok=False)


