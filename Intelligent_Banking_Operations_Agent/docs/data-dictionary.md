# Data Dictionary (Key Fields)

- event_id: UUID, unique identifier for event
- ts: ISO8601 timestamp
- type: enum {PAYMENT_AUTH, PAYMENT_CLEAR, CHARGEBACK, ...}
- account_id: string, internal account identifier
- amount: number, transaction amount
- currency: string, ISO 4217
- mcc: string, merchant category code
- merchant_id: string, internal/external merchant id
- channel: enum {WEB, APP, POS, ATM, P2P}
- device_id: string, fingerprint hash
- ip: string, IPv4/IPv6
- geo: object {lat, lon, country}
- auth: object {3ds, mfa_attempts}
- card: object {bin, country}
- labels: nullable, label object when available {fraud|genuine, source, ts}

Features (examples)
- velocity_1h_count/total, velocity_24h_count/total
- amount_zscore, device_novelty, geo_novelty, high_risk_mcc
- hour_of_day, is_night, first_time_mcc
