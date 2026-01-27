# Reference Architecture (Kappa, stream-first)

```mermaid
graph LR
  subgraph "Channels"
    A1["App/Web"] -->|"login, pay"| G
    A2["Merchant API"] --> G
    A3["Core Banking"] --> G
  end

  subgraph "Streaming Ingestion"
    G["Gateway/API"] --> EH[("Kafka/Event Hubs")]
    W["Webhooks (labels/chargebacks)"] --> EH
  end

  subgraph "Real-time Feature Platform"
    EH --> SS["Flink/Spark Streaming"]
    SS -->|"counters/velocities"| Redis[("Online Feature Store")]
    SS -->|"raw & hourly"| Lake[("ADLS/S3/GCS Bronze/Silver")]
    Lake --> Hive[("Offline Feature Store")]
  end

  subgraph "Identity Resolution & Graph"
    SS --> ER["Entity Resolver (email/phone/device)"]
    ER --> Graph[("Neo4j/Janus + GNN")]
    Graph --> Redis
  end

  subgraph "Model Dev & Registry"
    Hive --> Train["Training Jobs (GBDT + Anomaly + GNN)"]
    Train --> Reg["Model Registry (MLflow/AzML)"]
  end

  subgraph "Decisioning"
    Redis --> Score["Scoring Service (gRPC/REST)"]
    Reg --> Score
    Score --> Pol["Policy Engine (rules + thresholds)"]
    Pol --> D1["Approve"]
    Pol --> D2["Step-Up (MFA/3DS)"]
    Pol --> D3["Decline/Queue"]
    D3 --> Case["Case Mgmt + Analyst UI"]
    Case --> WQ["Labels/Outcomes"]
    WQ --> Lake
  end

  subgraph "Monitoring & Governance"
    Lake --> Mon["Metrics/Drift/Explainability"]
    Score --> Mon
    Pol --> Mon
  end
```

- Azure mapping: API Management + Event Hubs; ADLS Gen2; Databricks Structured Streaming or Flink on AKS; Azure Cache for Redis; Delta/Synapse + Feast; Azure ML/MLflow; AKS/Functions; CosmosDB (Gremlin)/Neo4j Aura; CosmosDB + Web App/AKS; App Insights + Prometheus/Grafana.
- GCP alt: Cloud Endpoints + Pub/Sub; BigQuery + GCS; Dataflow (Flink); MemoryStore (Redis); Feast + BigQuery; Vertex AI; Neo4j Aura/JanusGraph; Cloud Run/GKE; Cloud Monitoring.

Latency budgets
- Features: 50–100 ms online
- Score + policy: < 150 ms end-to-end
