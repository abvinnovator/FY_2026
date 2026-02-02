# Credit Risk System - Testing Guide

## How to Test This Application

This guide explains how to test the Credit Risk Analysis system step by step.

---

## 1. Prerequisites

Before testing, make sure you have:

1. **Model file ready**: `src/credit_risk/catboost_credit_model.cbm`
   - Run your Kaggle notebook and add this code to dump the model:

   ```python
   model.save_model('catboost_credit_model.cbm')
   ```

   - Download and place in `src/credit_risk/` folder

2. **Backend running**: `python -m uvicorn main:app --reload`

3. **Frontend running**: `cd frontend && npm run dev`

---

## 2. Test Cases

### Test Case 1: GOOD CUSTOMER (Expected: APPROVE)

**Frontend Input:**
| Field | Value |
|-------|-------|
| **Loan Type** | **Credit Card** |
| Monthly Income | $6,000 |
| Monthly Liabilities | $1,500 |
| Requested Limit | $2,000 |
| Credit Utilization | 25% |
| Delinquency Flags | (none) |

**What happens in backend:**

```
STEP 1: RAW INPUT FROM FRONTEND
  income             : $6,000.00
  liabilities        : $1,500.00
  requested_limit    : $2,000.00
  loan_type          : credit_card  <-- NEW
  delinquency_flags  : []
  credit_utilization : 25%

STEP 2: FEATURE ENGINEERING
  dti            : 0.2500 (25.0%)    ← Good: under 35%
  utilization    : 0.2500 (25.0%)    ← Good: low utilization
  limit_ratio    : 0.3333            ← OK: well within Credit Card limits (up to 300% for prime)
  delinquency    : 0                 ← Good: clean history

STEP 3: FUZZY LOGIC
  Fuzzy Score    : 80-90/100
  Fuzzy Band     : "excellent"
  Rules Fired    : ["Prime Applicant Bonus", "Low DTI Rule"]

STEP 4: FINAL DECISION
  Decision       : APPROVE
  Suggested Limit: ~$2,500 (Conservative)
```

---

### Test Case 4: PRODUCT LOGIC EDGE CASE (The "Prime Borrower" Test)

**Scenario**: A prime borrower asks for $15,000 limit with $12,000 income (125% ratio).

- **As BNPL**: Should DECLINE (Too high for BNPL)
- **As Personal Loan**: Should APPROVE (Acceptable for Personal Loan)

**Frontend Input:**
| Field | Value |
|-------|-------|
| Monthly Income | $12,000 |
| Requested Limit| $15,000 |
| Loan Type | **BNPL** vs **Personal Loan** |
| DTI | 2.5% (Excellent) |
| Utilization | 25% (Excellent) |

**Result Comparison:**

| Feature          | **BNPL** Outcome                 | **Personal Loan** Outcome           |
| :--------------- | :------------------------------- | :---------------------------------- |
| **Limit Policy** | **FAIL**: > 100% Income          | **PASS**: < 600% Income (for Prime) |
| **Decision**     | **DECLINE** (Policy BNPL-001)    | **APPROVE** (Prime Bonus Applied)   |
| **Reason**       | "Limit exceeds typical BNPL max" | "Prime Applicant - Approved"        |

_This proves the system understands the difference between different loan products!_

---

### Test Case 2: RISKY CUSTOMER (Expected: REVIEW)

**Frontend Input:**
| Field | Value |
|-------|-------|
| Monthly Income | $4,000 |
| Monthly Liabilities | $1,800 |
| Requested Limit | $3,000 |
| Credit Utilization | 65% |
| Delinquency Flags | 30+ days |

**What happens in backend:**

```
STEP 1: RAW INPUT FROM FRONTEND
  income             : $4,000.00
  liabilities        : $1,800.00
  requested_limit    : $3,000.00
  delinquency_flags  : ["30+ days"]
  credit_utilization : 65%

STEP 2: FEATURE ENGINEERING
  dti            : 0.4500 (45.0%)    ← Warning: above 35%
  utilization    : 0.6500 (65.0%)    ← Warning: high utilization
  limit_ratio    : 0.7500            ← Warning: high request
  delinquency    : 1                 ← Warning: 30 days late
  credit_history : 1                 ← 1 negative event

STEP 3: FUZZY LOGIC
  Fuzzy Score    : 45-55/100
  Fuzzy Band     : "fair"
  Rules Fired    : ["High DTI Warning", "Delinquency Penalty"]

STEP 4: ML MODEL
  Default Prob   : 0.35-0.45 (35-45%)
  ML Score       : 55-65/100
  Risk Level     : "Medium"

STEP 5: FUSION
  Fused Score    : ~55/100

STEP 6: FINAL DECISION
  Decision       : REVIEW
  Risk Level     : Medium-Low
```

---

### Test Case 3: HIGH RISK (Expected: DECLINE)

**Frontend Input:**
| Field | Value |
|-------|-------|
| Monthly Income | $3,000 |
| Monthly Liabilities | $2,100 |
| Requested Limit | $5,000 |
| Credit Utilization | 85% |
| Delinquency Flags | 90+ days, bankruptcy |

**What happens in backend:**

```
STEP 1: RAW INPUT
  income             : $3,000.00
  liabilities        : $2,100.00
  requested_limit    : $5,000.00
  delinquency_flags  : ["90+ days", "bankruptcy"]
  credit_utilization : 85%

STEP 2: FEATURE ENGINEERING
  dti            : 0.7000 (70.0%)    ← CRITICAL: above 60%
  utilization    : 0.8500 (85.0%)    ← CRITICAL: very high
  limit_ratio    : 1.6667            ← CRITICAL: requesting 167% of income
  delinquency    : 5                 ← CRITICAL: bankruptcy
  credit_history : 2                 ← Multiple negatives

STEP 3: FUZZY LOGIC
  Fuzzy Score    : 20-30/100
  Fuzzy Band     : "poor"

STEP 4: ML MODEL
  Default Prob   : 0.70-0.85 (70-85%)
  ML Score       : 15-30/100
  Risk Level     : "High"

STEP 5: FUSION
  Fused Score    : ~25/100

STEP 6: FINAL DECISION
  Decision       : DECLINE
  Hard Decline   : True
  Reason         : "Bankruptcy on record", "DTI exceeds 60%"
```

---

## 3. How to Validate Results

### Check if Decision is Correct:

| DTI    | Utilization | Delinquency | Expected Decision |
| ------ | ----------- | ----------- | ----------------- |
| < 35%  | < 50%       | None        | APPROVE           |
| 35-45% | 50-70%      | 30+ days    | REVIEW            |
| > 45%  | > 70%       | 60+ days    | DECLINE           |
| > 60%  | Any         | Any         | DECLINE (hard)    |
| Any    | Any         | Bankruptcy  | DECLINE (hard)    |

### Cross-Validate with ML Model:

1. Open your Kaggle notebook
2. Create same input:

   ```python
   test_input = pd.DataFrame([{
       'dti': 0.25,
       'utilization': 0.25,
       'limit_ratio': 0.33,
       'delinquency': 0,
       'credit_history': 0
   }])

   prob = model.predict_proba(test_input)[0][1]
   print(f"Default Probability: {prob:.4f}")
   ```

3. Compare with backend log output

### Cross-Validate Fuzzy Logic:

- DTI < 30% → Should give positive score
- DTI > 50% → Should give negative score
- Clean delinquency → "Clean Payment History" rule fires

---

## 4. Reading the Logs

When you test, watch the terminal running the backend. You'll see:

```
============================================================
RISK FUSION ENGINE - PROCESSING
============================================================
STEP 1: RAW INPUT FROM FRONTEND
  income             : $5,000.00
  liabilities        : $1,500.00
  ...

------------------------------------------------------------
STEP 2: FEATURE ENGINEERING (for ML Model)
  dti            : 0.3000 (30.0%)
  utilization    : 0.3500 (35.0%)
  ...

------------------------------------------------------------
STEP 3: FUZZY LOGIC (10 Rules)
  Fuzzy Score    : 65.0/100
  Fuzzy Band     : good
  Rules Fired    : ['Low DTI Rule']

------------------------------------------------------------
STEP 4: CATBOOST ML MODEL
==================================================
ML MODEL INPUT
==================================================
  dti            : 0.3000
  utilization    : 0.3500
  limit_ratio    : 0.4000
  delinquency    : 0
  credit_history : 0
--------------------------------------------------
ML MODEL OUTPUT
--------------------------------------------------
  Default Probability : 0.1823 (18.2%)
  Risk Level          : Low
  Top Risk Factors    : ['Debt-to-Income Ratio']
==================================================

------------------------------------------------------------
STEP 5: FUSION (Weighted Average)
  Fuzzy Weight   : 50%
  ML Weight      : 50%
  Fused Score    : (50% × 65.0) + (50% × 81.8) = 73.4

------------------------------------------------------------
STEP 6: FINAL DECISION
  Decision         : APPROVE
  Final Score      : 73.4/100
  Risk Level       : Medium-Low
  Confidence       : 95%
============================================================
```

---

## 5. Quick Reference

### ML Model Features:

| Feature        | Description        | Range |
| -------------- | ------------------ | ----- |
| dti            | Debt-to-Income     | 0-1   |
| utilization    | Credit Utilization | 0-1   |
| limit_ratio    | Requested/Income   | 0-2+  |
| delinquency    | Delinquency Level  | 0-5   |
| credit_history | Negative Count     | 0-6   |

### Decision Thresholds:

| Score           | Decision |
| --------------- | -------- |
| ≥ 65            | APPROVE  |
| 45-64           | REVIEW   |
| < 45            | DECLINE  |
| Any + Hard Rule | DECLINE  |

- DTI ≥ 60%
- Bankruptcy on record
- Charge-off on record

---

## 6. Understanding the Inputs

| Input Field             | Meaning                                                       | Why it matters?                                                            | Good Range               |
| :---------------------- | :------------------------------------------------------------ | :------------------------------------------------------------------------- | :----------------------- |
| **Monthly Income**      | Total gross monthly earnings before taxes.                    | Determines your base capacity to pay back loans.                           | Higher is better.        |
| **Monthly Liabilities** | Current monthly debt payments (EMIs, rent, credit card mins). | Used to calculate DTI (Debt-to-Income). High debt reduces repayment power. | < 30% of income.         |
| **Requested Limit**     | Total credit limit you are asking for.                        | High requests relative to income increase risk of "over-leveraging."       | < 50% of monthly income. |
| **Credit Utilization**  | Current credit card balance divided by total limits.          | Shows how much of your existing credit you've already "maxed out."         | < 30%.                   |
| **Delinquency Flags**   | History of late payments (30, 60, 90+ days late).             | The strongest indicator of future default. Bankruptcy is a major red flag. | Clean (No flags).        |
| **Employment Months**   | Total months at your current job.                             | Banks prefer stable income sources. Job hopping increases risk.            | > 24 months (2 years).   |
| **History Months**      | Age of your oldest credit account.                            | A long "track record" gives banks more confidence in your behavior.        | > 36 months (3 years).   |

## 8. New Terminal Logs Flow

When you click "Analyze Risk" in the frontend, your **Backend Terminal** will now show exactly what happened in real-time:

1.  **🚀 FUZZY LOGIC TRIGGERED**: Shows raw inputs and which of the 10 rules (from `rules.json`) were activated.
2.  **🧠 ML LOGIC TRIGGERED**: Shows the CatBoost model processing the same inputs to get a "Default Probability."
3.  **🤖 LLM TRIGGERED**: Shows the Gemini model receiving the math and writing the professional Underwriter rationale.

_This makes the system 100% transparent for your final presentation!_
