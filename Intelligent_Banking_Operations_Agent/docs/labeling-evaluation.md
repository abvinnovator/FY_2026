# Labeling & Evaluation Playbook

Labels
- Source: chargebacks, disputes, SARs/AML, analyst outcomes
- Latency buffers: pending labels queue; weak labels (claims) gated

DAG
- Ingest events → queue pending → receive labels (webhooks/manual) → join on event_id → write gold set

Class imbalance
- Cost-sensitive learning, focal loss or class weights; SMOTE for experiments
- Validate with PR-AUC and cost metrics; report VDR (value per decision)

Operational metrics
- PR-AUC, Recall@Alert-Budget, approval rate, false positive rate, AHT
- Confusion matrix per band and channel; band distribution
