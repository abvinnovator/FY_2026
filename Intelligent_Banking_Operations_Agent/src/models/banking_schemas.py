from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Transaction(BaseModel):
	txn_id: str = Field(default_factory=lambda: "")
	account_id: str
	amount: float
	currency: str = "USD"
	merchant: str | None = None
	mcc: str | None = None
	geo: str | None = None
	device_id: str | None = None
	channel: str | None = None
	timestamp: datetime
	features: dict[str, Any] | None = None
	labels: dict[str, Any] | None = None


class Alert(BaseModel):
	alert_id: str = Field(default_factory=lambda: "")
	txn_id: str
	scores: dict[str, float]
	rule_hits: list[str]
	decision: str
	rationale: str
	reviewer: str | None = None
	state: str = "open"
	created_at: datetime = Field(default_factory=datetime.utcnow)


class CreditApplication(BaseModel):
	app_id: str = Field(default_factory=lambda: "")
	applicant_profile: dict[str, Any]
	derived_features: dict[str, Any] | None = None
	score: float | None = None
	decision: str | None = None
	rationale: str | None = None


class PolicyDocument(BaseModel):
	doc_id: str
	title: str
	embedding: list[float] | None = None
	text: str
	section_refs: list[str] | None = None


class AuditLog(BaseModel):
	agent_name: str
	action: str
	input_refs: dict[str, Any]
	output_refs: dict[str, Any]
	timestamp: datetime = Field(default_factory=datetime.utcnow)


