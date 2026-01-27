# Modeling Strategy (Hybrid)

1) Baseline supervised (week 2–3): LightGBM/XGBoost with class weights; PR-AUC and cost metrics.
2) Anomaly side-car: IsolationForest/Autoencoder; send to low-confidence queue; lower weight.
3) Graph boost (phase 2): R-GCN/GraphSAGE signal (distance to rings) as feature or stage-2.
4) Policy engine: immutable hard-stops then threshold bands.

Explainability
- SHAP at inference (top-5 features) and global monitoring dashboards.
