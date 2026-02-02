# 🧠 Fuzzy Logic Credit Scoring System – Detailed Explanation

This document explains **how the fuzzy logic credit score is calculated** in your application and **how policy violations override the score**, with **clear examples**. This is written to be understandable by **students, developers, and bankers**.

---

## 1️⃣ What This System Is (In One Line)

> This system **does not calculate credit score using a fixed formula**. Instead, it mimics how banks think by combining **human-style rules (fuzzy logic)** with **strict policy checks**.

---

## 2️⃣ Raw Inputs (What the Applicant Gives)

Examples of raw inputs:

- Monthly Income
- Monthly Liabilities
- Credit Utilization (%)
- Delinquency history (30/60/90 days, bankruptcy, etc.)
- Employment duration
- Credit history length
- Requested credit limit
- Age

These values **do not directly produce a credit score**.

---

## 3️⃣ DTI Calculation (Only Pure Math Part)

DTI is calculated using a **simple formula**:

```
DTI = liabilities / income
```

### Example

```
Income      = 50,000
Liabilities = 20,000

DTI = 20,000 / 50,000 = 0.40 → 40%
```

This DTI value is later used as an **input to fuzzy logic**, not as a score.

---

## 4️⃣ Fuzzy Logic Overview (High Level)

Fuzzy logic works in **four stages**:

1. **Fuzzification** – Convert numbers into linguistic meanings
2. **Rule Evaluation** – Apply IF–THEN banking rules
3. **Aggregation** – Combine rule outputs
4. **Defuzzification** – Convert fuzzy output into a number (0–100)

---

## 5️⃣ Step 1: Fuzzification (Converting Numbers to Meaning)

Each numeric input is mapped into **degrees of membership**.

### Example: DTI = 40%

| Linguistic Term | Membership Degree |
|---------------|------------------|
| excellent | 0.0 |
| good | 0.3 |
| moderate | 0.7 |
| high | 0.0 |
| critical | 0.0 |

Meaning:
> Applicant is **70% moderate DTI** and **30% good DTI**.

This same fuzzification happens for **all inputs**.

---

## 6️⃣ Step 2: Rule Evaluation (Human Banking Logic)

Each rule looks like:

```
IF DTI is moderate
AND Credit Utilization is good
AND Delinquency is clean
THEN Credit Score is GOOD
```

### Rule Firing Strength Calculation

- AND → `min()`
- OR → `max()`

### Example

```
DTI (moderate)        = 0.7
Utilization (good)   = 0.8
Delinquency (clean)  = 1.0

Rule firing strength = min(0.7, 0.8, 1.0) = 0.7
```

This rule contributes **0.7 strength** to the output term **GOOD**.

---

## 7️⃣ Step 3: Aggregation (Mamdani MAX)

After evaluating all 10 rules, outputs look like this:

| Output Term | Final Activation |
|------------|------------------|
| very_poor | 0.1 |
| poor | 0.2 |
| fair | 0.5 |
| good | 0.7 |
| excellent | 0.3 |

Only the **maximum strength per output category** is retained.

---

## 8️⃣ Step 4: Defuzzification (Final Credit Score)

Each output term has a **fixed centroid value**:

| Credit Term | Centroid |
|------------|----------|
| very_poor | 15 |
| poor | 35 |
| fair | 55 |
| good | 75 |
| excellent | 92 |

### Final Fuzzy Score Formula

```
Final Score =
(15×very_poor + 35×poor + 55×fair + 75×good + 92×excellent)
/ (sum of all activations)
```

### Example Calculation

```
= (15×0.1 + 35×0.2 + 55×0.5 + 75×0.7 + 92×0.3)
/ (0.1+0.2+0.5+0.7+0.3)

= 71.8
```

✅ **This is the raw fuzzy credit score**.

---

## 9️⃣ Policy Violations (Hard Rules – Override Everything)

Even if fuzzy score is high, **policy violations automatically force decline**.

### Examples of Policy Rules

| Condition | Effect |
|---------|-------|
| DTI ≥ 60% | Decline |
| 90+ DPD | Decline |
| Bankruptcy | Decline |
| Requested limit ≥ 200% income | Decline |
| Credit utilization ≥ 90% | Decline |

### Example

```
Fuzzy Score = 78
DTI = 65%
```

Result:
```
Policy Violation: DTI > 60%
Final Decision: DECLINE
Final Score capped at 25
```

👉 **Policy rules override fuzzy logic completely**.

---

## 🔟 Final Decision Logic

| Final Score | Decision |
|------------|----------|
| ≥ 75 | Approve |
| 60–74 | Approve |
| 45–59 | Review |
| < 45 | Decline |

⚠️ **If any policy violation exists → Decline**, regardless of score.

---

## 1️⃣1️⃣ Key Takeaways (Very Important)

- DTI is **calculated mathematically**
- Credit score is **not a formula**
- Credit score comes from **rule activations**
- Policy rules are **absolute and final**
- System mimics **real bank underwriting**

---

## 1️⃣2️⃣ One-Line Summary (For Interview / Docs)

> The system calculates DTI using income and liabilities, applies fuzzy logic rules to convert applicant risk into a numeric score, and finally enforces strict banking policies that can override and automatically decline applications.

---

**End of Document**

