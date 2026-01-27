# Data Contracts

## Transaction event (stream)

```json
{
  "event_id":"uuid",
  "ts":"2025-08-25T11:47:00Z",
  "type":"PAYMENT_AUTH",
  "account_id":"A123",
  "amount": 4999.00,
  "currency":"INR",
  "mcc":"5812",
  "merchant_id":"M789",
  "channel":"WEB",
  "device_id":"d_hash",
  "ip":"203.0.113.10",
  "geo":{"lat":17.44,"lon":78.39,"country":"IN"},
  "auth":{"3ds":"CHALLENGE_SUCCESS","mfa_attempts":1},
  "card":{"bin":"510510","country":"IN"},
  "labels": null
}
```

## Score request → response

Request
```json
{"event_id":"uuid","account_id":"A123","feature_keys":["acc_txn_1h","ip_risk","device_stability","graph_dist_fraud"]}
```

Response
```json
{"event_id":"uuid","risk_score":0.87,"reason_codes":["ip_risk","new_device","high_velocity"],"model":"lgbm_v12","latency_ms":14}
```
