# Feature Spec

Transaction/behavioral
- Amount deltas, z-score, MCC entropy, merchant baselines
- Velocity per 1h/24h, declines ratio, first-time MCC
- Hour-of-day, geo-distance vs last good

Device/network/session
- Device fingerprint stability, proxy/VPN/TOR flag, IP ASN risk
- Emulator/jailbreak, cookie reuse; SIM-swap recency (telco feed)

Identity & lifecycle
- Email/phone tenure, address age, recent profile edits
- MFA failures, password resets, delivery address velocity

Graph-level
- Shared device/phone/email/address/card; degree, PageRank, triangle count
- Distance to known fraud, community score; GNN embeddings

Context
- Holiday/event spikes, BIN–IP country mismatch, watchlist hits

Owners & freshness
- Real-time (Redis): counters, velocities, novelty; freshness 1–5 minutes
- Offline (Hive/Feast): merchant baselines, graph scores; refreshed hourly/daily
