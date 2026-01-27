from __future__ import annotations

from typing import Any, TypedDict, Literal

from langgraph.graph import StateGraph, END

from src.agents.banking_supervisor import BankingSupervisor
from src.agents.fraud_triage_agent import FraudTriageAgent
from time import perf_counter
from uuid import uuid4
from datetime import datetime
from src.fraud_detection.telemetry import record_event, TriageEvent
from src.agents.credit_risk_agent import CreditRiskAgent


class TriageState(TypedDict, total=False):
	payload: dict[str, Any]
	intent: Literal["fraud", "credit", "operations"]
	result: dict[str, Any]


def supervisor_node(state: TriageState) -> dict[str, Any]:
	supervisor = BankingSupervisor()
	decision = supervisor.classify(state["payload"])
	return {"intent": decision.intent}


def fraud_node(state: TriageState) -> dict[str, Any]:
	payload = state["payload"]
	started = perf_counter()
	agent = FraudTriageAgent()
	result = agent.triage(
		amount=float(payload.get("amount", 0.0)),
		mcc=payload.get("mcc"),
		geo=payload.get("geo"),
		device_id=payload.get("device_id"),
		history=[],
	)
	sla_ms = int((perf_counter() - started) * 1000)
	event_id = str(uuid4())
	# Build human-friendly explanations and summary for unified endpoint - COMMENTED OUT
	features = getattr(result, "features", {}) or {}
	explanations: list[str] = []
	# if features.get("amount_zscore", 0.0) >= 3.5:
	# 	explanations.append(f"Transaction amount is {features['amount_zscore']:.1f}σ above the account's average")
	# if features.get("geo_novelty", 0.0) >= 1.0:
	# 	explanations.append("Transaction originates from a new or high-risk geographical location")
	# if features.get("device_novelty", 0.0) >= 1.0:
	# 	explanations.append("Device ID has not been seen on this account before")
	# if features.get("high_risk_mcc", 0.0) >= 1.0 and payload.get("mcc"):
	# 	explanations.append(f"Merchant Category ({payload.get('mcc')}) is flagged as high-risk")
	# if features.get("velocity_1h_count", 0.0) >= 5:
	# 	explanations.append("High transaction velocity in the last 1 hour")
	# for hit in getattr(result, "rule_hits", []) or []:
	# 	if hit not in explanations:
	# 		explanations.append(hit)
	risk_score = round(float(getattr(result, "alert_score", 0.0)) * 100)
	risk_band = getattr(result, "risk_band", "low")
	risk_label = risk_band.capitalize()
	decision_human = "Manual review recommended" if risk_band in {"medium", "high"} else "Approve"
	summary = f"{risk_label} Risk ({risk_score}/100): {decision_human}."
	# Record telemetry
	record_event(TriageEvent(
		event_id=event_id,
		timestamp_s=datetime.utcnow().timestamp(),
		intent="fraud",
		payload=dict(payload),
		decision=str(result.decision),
		risk_band=str(result.risk_band),
		alert_score=float(result.alert_score),
		explanations=list(explanations),
		features=features,
		sla_ms=sla_ms,
	))

	return {
		"result": {
			"event_id": event_id,
			"alert_score": result.alert_score,
			"decision": result.decision,
			"rationale": result.rationale,
			"policy_citations": result.policy_citations,
			"features": features,
			"risk_band": result.risk_band,
			"explanations": explanations,
			"summary": summary,
			"rule_hits": getattr(result, "rule_hits", []),
			"sla_ms": sla_ms,
		},
	}


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
	if intent == "fraud":
		return "fraud"
	if intent == "credit":
		return "credit"
	return "credit"  # default


def build_triage_graph():
	graph = StateGraph(TriageState)
	graph.add_node("supervisor", supervisor_node)
	graph.add_node("fraud", fraud_node)
	graph.add_node("credit", credit_node)
	graph.set_entry_point("supervisor")
	graph.add_conditional_edges(
		"supervisor",
		_route_by_intent,
		{
			"fraud": "fraud",
			"credit": "credit",
		},
	)
	graph.add_edge("fraud", END)
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



