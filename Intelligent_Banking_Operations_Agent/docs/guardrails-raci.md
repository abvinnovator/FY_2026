# Guardrails & RACI

Regulatory envelope
- PCI DSS scope and tokenization for PAN; avoid storing sensitive auth data
- Local privacy law (e.g., India DPDP 2023): purpose limitation, retention, consent
- RBI Digital Payment Security Controls alignment (secure APIs, separation of duties)

Model/policy governance
- Change control with approvals; versioned thresholds and rules
- Annual audits; model documentation/model cards
- Telemetry: feature snapshots, decisions, overrides, labels; retention per policy

RACI
- Product: Accountable for scope, metrics, customer impact
- Risk: Responsible for thresholds, hard-stops, escalation
- Engineering: Responsible for implementation and SLOs
- Compliance: Consulted for regulatory alignment and audits
- Operations/Analyst: Responsible for labeling, SOPs; Informed on changes
