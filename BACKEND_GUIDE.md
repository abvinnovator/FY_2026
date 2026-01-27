# 🏦 Backend Architecture & Logic Guide

This document explains the **Backend (FastAPI)** structure of the Intelligent Banking Operations Agent. It covers every major folder and file, explaining the "logic" behind how the system processes data.

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

- **`config.py`**: Managing "Secrets." It uses Pydantic to read your `.env` file (like your Gemini/OpenAI keys) and makes them available to the entire app.
- **`database.py`**: The Connection Hub.
  - **MongoDB**: The project is _prepared_ to use MongoDB for saving long-term data (like transaction history), though for the "Live Demo," most data is processed in memory.
  - **Redis**: Prepared for "Caching" to make the system super fast.
- **`logging_config.py`**: Controls the "Terminal Output." It ensures that every action is logged so developers can debug issues.

---

## 🤖 2. The Agents (The Brains)

### **`src/agents/`**

This is where the High-Level AI logic lives.

- **`fraud_triage_agent.py`**: Coordinates the fraud check. It calls the "Rule Engine," then the "ML Anomaly Detector," and finally uses **Gemini** to explain the result.
- **`credit_risk_agent.py`**: Coordinates the loan check. It calculates DTI, checks the Scorecard, and uses **Gemini** to write the approval/rejection letter.
- **`langgraph_workflow.py`**: The **Orchestrator**. It uses a "Graph" to decide which agent to call. If you send transaction data, it routes to Fraud. If you send application data, it routes to Credit.
- **`banking_supervisor.py`**: The "Router." It's a simpler version of the orchestrator that looks at the incoming data and classifies it as "Fraud," "Credit," or "General Operations."

---

## 🔍 3. Data Processing (The Mechanics)

### **`src/fraud_detection/`**

- **`rule_engine.py`**: The "Lawbook." Contains hardcoded mathematical rules (e.g., "Flag if amount is > 5 standard deviations from normal").
- **`iforest_model.py` (The ML Model)**:
  - **ML Used? YES!** This file uses an **Isolation Forest** (a Machine Learning algorithm) to detect "unusual" patterns that rules might miss. It's great at finding "Outliers."
- **`feature_engineering.py`**: The "Translator." It takes raw data (like "Amount: $100") and turns it into math (like "Z-Score: 1.5").
- **`telemetry.py`**: The "Memory." It records every decision made so you can see them in the "Analytics" tab.

### **`src/credit_risk/`**

- **`scorecard.py`**: The "Grading System." It assigns points based on DTI and Delinquency Flags.
- **`affordability_calculator.py`**: Computes the **DTI** (Debt-to-Income) and suggests how much the bank should safely lend.

---

## 📚 4. RAG & Policy

### **`src/rag/`**

- **`retriever.py`**: The "Librarian." When the AI needs a rule, this file searches your `data/policies/` folder.
- **`vector_store`**: (Generated folder) This is a "Vector Database" (ChromaDB). It stores the text of your policies in a format that AI can search through "meaning" rather than just keywords.

---

## 📝 5. Communication (The API)

### **`src/channels/`**

- **`banking_api_routes.py`**: The "Counter."
  - It defines the URLs the frontend calls (like `/api/v1/triage`).
  - It validates that the data sent by the browser is in the correct format using **Pydantic Models**.

---

## ❓ Common Questions

**Does it use MongoDB?**
**Yes and No.** The code _supports_ it (see `src/core/database.py`), but for this project's demo mode, we use **In-Memory** storage and the **ChromaDB Vector Store** to make it easy to run without requiring you to install a heavy database like Mongo.

**What is the logic flow?**

1. Request arrives at `banking_api_routes.py`.
2. Routed via `langgraph_workflow.py`.
3. Specialized Agent (`Credit` or `Fraud`) calculates math/rules.
4. `Retriever` finds relevant policy text.
5. `Gemini` combines everything and responds.
