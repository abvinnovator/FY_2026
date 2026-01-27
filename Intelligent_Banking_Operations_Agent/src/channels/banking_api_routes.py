from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.langgraph_workflow import TriageOrchestrator
from src.fraud_detection.telemetry import compute_kpis

router = APIRouter(tags=["banking"])


class TransactionInput(BaseModel):
	account_id: str
	amount: float
	currency: str | None = "USD"
	merchant: str | None = None
	mcc: str | None = None
	geo: str | None = None
	device_id: str | None = None
	channel: str | None = None
	timestamp: str | None = None


class ApplicationInput(BaseModel):
	applicant_id: str
	income: float
	liabilities: float
	delinquency_flags: list[str] | None = []
	requested_limit: float | None = None

@router.post("/credit/triage")
async def credit_triage(input_app: ApplicationInput):
	agent = CreditRiskAgent()
	res = agent.triage(
		income=input_app.income,
		liabilities=input_app.liabilities,
		delinquency_flags=input_app.delinquency_flags,
		requested_limit=input_app.requested_limit,
	)
	return {
		"score": res.score,
		"decision": res.decision,
		"rationale": res.rationale,
		"policy_citations": res.policy_citations,
		"key_factors": res.key_factors,
	}


@router.get("/analytics/kpis")
async def analytics_kpis():
	return compute_kpis()



class TriageInput(BaseModel):
	payload: dict


@router.post("/triage")
async def unified_triage(body: TriageInput):
	orchestrator = TriageOrchestrator()
	result = orchestrator.invoke(body.payload)
	return result
