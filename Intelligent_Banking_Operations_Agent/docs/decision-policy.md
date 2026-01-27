# Decision Matrix & SCA Policy

- Approve: risk_score < medium threshold; no hard-stops; complies with TRA bands.
- Step-Up: medium ≤ risk_score < high; trigger MFA/3DS; log TRA telemetry.
- Decline/Queue: risk_score ≥ high or hard-stop rules; create case for review.

Hard-stop examples
- Sanctions/watchlist match
- Impossible travel (geo-time)
- Synthetic identity flags

PSD2/TRA considerations
- Maintain fraud-rate thresholds per instrument and exemption category
- Annual audits, model change control, telemetry retention
- Evidence store of TRA decisions with features and outcomes
