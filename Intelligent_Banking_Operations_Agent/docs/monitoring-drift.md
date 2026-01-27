# Monitoring, Drift & Retraining

Performance metrics
- PR-AUC, Recall@Alert-Budget, VDR/monetary savings, approval rate, FPR, AHT
- SLA (p50/p95 latency), throughput, error rates

Drift detection
- Covariate drift: PSI, KS; detectors ADWIN/KSWIN/Page-Hinkley
- Concept drift: label delay handling; rolling window metrics

Retraining
- Scheduled weekly/monthly; trigger on drift alarms or KPI regressions
- Champion/challenger with shadow deploy; rollback plan

Observability
- App Insights/Prometheus; dashboards for features, bands, confusion; alerting
