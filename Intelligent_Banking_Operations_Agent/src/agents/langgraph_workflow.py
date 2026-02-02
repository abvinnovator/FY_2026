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
	"""
	Fraud Triage Node with Novel Features:
	- Risk Factor Breakdown
	- Anomaly Score Analysis
	- Recommended Actions
	"""
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
	
	features = result.features or {}
	risk_score = round(float(result.alert_score) * 100)
	risk_band = result.risk_band
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
		explanations=result.rule_hits,
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
			"rule_hits": result.rule_hits,
			"summary": summary,
			"sla_ms": sla_ms,
			# Novel fields
			"risk_factors": result.risk_factors,
			"anomaly_breakdown": result.anomaly_breakdown,
			"recommended_actions": result.recommended_actions,
		},
	}


def credit_node(state: TriageState) -> dict[str, Any]:
	"""
	Credit Risk Node with Novel Features:
	- Factor Contribution Analysis
	- What-If Scenarios
	- Improvement Recommendations
	"""
	payload = state["payload"]
	income = float(payload.get("income", 0.0))
	liabilities = float(payload.get("liabilities", 0.0))
	
	agent = CreditRiskAgent()
	res = agent.triage(
		income=income,
		liabilities=liabilities,
		delinquency_flags=list(payload.get("delinquency_flags", []) or []),
		requested_limit=(float(payload.get("requested_limit")) if payload.get("requested_limit") is not None else None),
		credit_utilization=payload.get("credit_utilization"),
		credit_history_months=payload.get("credit_history_months"),
		employment_months=payload.get("employment_months"),
		age=payload.get("age"),
	)
	
	# Calculate DTI for display
	dti = round((liabilities / income * 100), 1) if income > 0 else 0
	limit_suggested = round(income * 0.25, 2)
	
	return {
		"result": {
			"score": res.score,
			"decision": res.decision,
			"rationale": res.rationale,
			"policy_citations": res.policy_citations,
			"key_factors": res.key_factors,
			"dti": f"{dti}%",
			"limit_suggested": limit_suggested,
			# Novel fields
			"factor_breakdown": res.factor_breakdown,
			"improvement_tips": res.improvement_tips,
			"what_if_scenarios": res.what_if_scenarios,
			"risk_summary": res.risk_summary,
			# Fuzzy/Policy fields
			"fuzzy_score": res.fuzzy_score,
			"fuzzy_rules": res.fuzzy_rules_fired,
			"fuzzy_dominant_rules": res.fuzzy_dominant_rules,
			"policy_violations": res.policy_violations,
			"hard_decline": res.hard_decline,
			"hard_decline_reason": res.hard_decline_reason,
		},
	}


def _route_by_intent(state: TriageState) -> str:
	intent = state.get("intent")
	if intent == "fraud":
		return "fraud"
	if intent == "credit":
		return "credit"
	return "credit"  # default to credit


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
