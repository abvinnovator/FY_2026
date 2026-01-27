# 🏦 Backend Architecture & Logic Guide

This document explains the **Backend (FastAPI)** structure of the Intelligent Banking Operations Agent. It covers every major folder and file, explaining the "logic" behind how the system processes data.

> **Note**: As per the latest project refinement, the **Fraud Triage** functionality has been disabled/omitted to focus exclusively on **Credit Risk Assessment**.

---

## 🏗️ 1. Core Architecture (The Foundation)

### **`main.py`**

- **The Entry Point**: This is the heart of the FastAPI application.
- **What it does**:
  - Initializes the `FastAPI` app.
  - Sets up **CORS** (Cross-Origin Resource Sharing) so your Frontend can talk to the Backend.
  - Loads the **API Routes** (from `src/channels/`).
  - Handles the lifecycle (startup and shutdown) of the application.

### **`src/core/`**

- **`config.py`**: Managing "Secrets." It uses Pydantic to read your `.env` file (like your Gemini key) and makes them available to the entire app.
- **`database.py`**: The Connection Hub.
  - **MongoDB**: The project is _prepared_ to use MongoDB for saving long-term data (like transaction history), though for the "Live Demo," most data is processed in memory.
  - **Redis**: Prepared for "Caching" to make the system super fast.
- **`logging_config.py`**: Controls the "Terminal Output." It ensures that every action is logged so developers can debug issues.

---

## 🤖 2. The Agents (The Brains)

### **`src/agents/`**

This is where the High-Level AI logic lives.

- **`credit_risk_agent.py`**: Coordinates the loan check. It calculates DTI, checks the Scorecard, and uses **Gemini** to write the approval/rejection rationale.
- **`langgraph_workflow.py`**: The **Orchestrator**. It uses a "Graph" (State Machine) to process requests. Currently optimized to route all operations toward the Credit Risk evaluation.
- **`banking_supervisor.py`**: The "Router." It looks at the incoming data and classifies its intent. It now focuses on identifying Credit Risk applications.
- **`fraud_triage_agent.py`**: _(Disabled)_ Previously handled fraud detection logic using ML and rules.

---

## 🔍 3. Data Processing (The Mechanics)

### **`src/credit_risk/`**

- **`scorecard.py`**: The "Grading System." It assigns points based on DTI and Delinquency Flags.
- **`affordability_calculator.py`**: Computes the **DTI** (Debt-to-Income) and suggests how much the bank should safely lend.

### **`src/fraud_detection/`** _(Maintenance Mode)_

- **`iforest_model.py`**: Uses an **Isolation Forest** (Machine Learning algorithm) to detect anomalous transaction patterns.
- **`rule_engine.py`**: Contains hardcoded mathematical rules for fraud (e.g., Z-Score checks).
- **`telemetry.py`**: Records decisions for analytics.

---

## 📚 4. RAG & Policy

### **`src/rag/`**

- **`retriever.py`**: The "Librarian." When the AI needs a rule, this file searches the `data/policies/` folder.
- **`vector_store`**: (Generated folder) This is a "Vector Database" (ChromaDB). It stores the text of your policies in a format that AI can search through "meaning" rather than just keywords.

---

## 📝 5. Communication (The API)

### **`src/channels/`**

- **`banking_api_routes.py`**: The "Interface."
  - Defines URLs like `/api/v1/credit/triage`.
  - Validates that the data sent by the browser is correct using **Pydantic Models**.
  - **Note**: Fraud-related endpoints have been commented out to focus on Credit Risk.

---

## ❓ Common Questions

**Does it use MongoDB?**
**Yes and No.** The code _supports_ it (see `src/core/database.py`), but for the demo, we use **In-Memory** storage and the **ChromaDB Vector Store** to avoid external dependencies.

**What is the logic flow?**

1. Request arrives at `banking_api_routes.py`.
2. Routed via `langgraph_workflow.py` (Orchestrator).
3. The **Credit Agent** calculates math (DTI, Scorecard).
4. `Retriever` finds relevant banking policy text from the knowledge base.
5. **Gemini** combines the math + the policy to write a professional explanation.
6. The result is returned to the Frontend.
