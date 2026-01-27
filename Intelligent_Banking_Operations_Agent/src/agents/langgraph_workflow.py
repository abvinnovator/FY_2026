from __future__ import annotations

from typing import Any, TypedDict, Literal

from langgraph.graph import StateGraph, END

from src.agents.banking_supervisor import BankingSupervisor
from time import perf_counter
from uuid import uuid4
from datetime import datetime
from src.agents.credit_risk_agent import CreditRiskAgent


class TriageState(TypedDict, total=False):
	payload: dict[str, Any]
	intent: Literal["fraud", "credit", "operations"]
	result: dict[str, Any]


def supervisor_node(state: TriageState) -> dict[str, Any]:
	supervisor = BankingSupervisor()
	decision = supervisor.classify(state["payload"])
	return {"intent": decision.intent}


# Fraud node removed to focus on Credit Risk
# def fraud_node(state: TriageState) -> dict[str, Any]:
#    ...

def credit_node(state: TriageState) -> dict[str, Any]:
	payload = state["payload"]
	agent = CreditRiskAgent()
	res = agent.triage(
		income=float(payload.get("income", 0.0)),
		liabilities=float(payload.get("liabilities", 0.0)),
		delinquency_flags=list(payload.get("delinquency_flags", []) or []),
		requested_limit=(float(payload.get("requested_limit")) if payload.get("requested_limit") is not None else None),
	)
	return {
		"result": {
			"score": res.score,
			"decision": res.decision,
			"rationale": res.rationale,
			"policy_citations": res.policy_citations,
			"key_factors": res.key_factors,
		},
	}


def _route_by_intent(state: TriageState) -> str:
	intent = state.get("intent")
	# If intentional fraud is requested, we currently default to credit or handle gracefully
	if intent == "credit":
		return "credit"
	return "credit"  # Default everything to credit since fraud is removed


def build_triage_graph():
	graph = StateGraph(TriageState)
	graph.add_node("supervisor", supervisor_node)
	graph.add_node("credit", credit_node)
	graph.set_entry_point("supervisor")
	graph.add_conditional_edges(
		"supervisor",
		_route_by_intent,
		{
			"credit": "credit",
		},
	)
	graph.add_edge("credit", END)
	return graph.compile()


class TriageOrchestrator:
	def __init__(self) -> None:
		self.app = build_triage_graph()

	def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
		state_in: TriageState = {"payload": payload}
		state_out = self.app.invoke(state_in)
		out = dict(state_out.get("result", {}))
		out["intent"] = state_out.get("intent")
		return out
