# 🏦 Banking Concepts & System Guide (For Everyone)

This guide explains how our project works using simple, non-technical language. If you've never worked in a bank, this is for you!

---

## 1. Key Banking Terms Explained 📖

### **DTI (Debt-to-Income Ratio)**

This is the most important number in lending!

- **Simple Meaning**: What percentage of your monthly salary goes toward paying back debts (like other loans or credit cards)?
- **The Math**: If you earn **$4,000** a month and you pay **$1,200** in other loans, your DTI is **30%** ($1,200 ÷ $4,000).
- **The Rule**:
  - **35% or less**: Great! You have plenty of money left over.
  - **50% or more**: Risky. You might struggle to pay back a new loan.
  - **60% (The Hard Limit)**: In our system's policy, anything above 60% is an automatic "Alert" for manual review.

### **Requested Limit**

- **Simple Meaning**: This is the **amount of money** the user wants to borrow.
- **How we use it**: We compare this to their income. If someone earns $1,000 but asks for a $10,000 credit limit, our system flags it because they are asking for 10x their monthly salary!

### **MCC (Merchant Category Code)**

- **Simple Meaning**: A 4-digit code that tells us what _kind_ of shop a transaction happened at.
- **Example**: `5411` is a Grocery Store (Low Risk). `7995` is Gambling (High Risk).

---

## 2. How the System Works (The "Three-Layer" Logic) ⚙️

Our system doesn't just "guess." It follows three distinct steps every time you click a button:

### **Step 1: The Rule Check (The "Gatekeeper")**

Before the AI even looks at the data, our Python code checks hardcoded rules (in `rule_engine.py` and `scorecard.py`).

- _Example_: "If DTI is > 60%, flag it."
- This is fast, transparent, and always consistent.

### **Step 2: The RAG Search (The "Library Search")** 📚

**RAG** stands for _Retrieval-Augmented Generation_. Think of it as an AI that has a library of rulebooks.

1.  The system looks at the transaction (e.g., a $5,000 transfer).
2.  It "searches" the `data/policies/` folder for relevant text.
3.  It finds the `AML.txt` (Anti-Money Laundering) policy which says "Flags transfers over $4,000."
4.  It hands this specific rule to the Gemini AI so the AI knows the bank's actual laws.

### **Step 3: The Gemini AI (The "Decision Expert")** 🧠

Now that Gemini has the **Data** and the **Rules (from RAG)**, it writes the rationale.

- _Without AI_: The system would just say "Reject: Rule 4.4." (Boring and unhelpful).
- _With Gemini_: It says: "We are declining this because the applicant's DTI is 65%, which exceeds our 60% safety limit. This ensures the customer doesn't take on more debt than they can handle."

---

## 3. The Backend Structure (Simply Put) 🏗️

| Folder                     | What it does                                                          |
| :------------------------- | :-------------------------------------------------------------------- |
| **`src/agents/`**          | The "Brains." Contains the Fraud and Credit agents.                   |
| **`src/fraud_detection/`** | The "Detection Lab." Calculates if a transaction is weird.            |
| **`src/credit_risk/`**     | The "Calculator." Works out the DTI and Credit Scores.                |
| **`data/policies/`**       | The "Rulebook." Flat text files that the AI reads to stay "grounded." |

---

## 4. Why is this useful? 🚀

In the real world, a human loan officer can only review about 20-30 applications a day. Our system can review **thousands per second**.

It automatically approves the "Safe" ones and only sends the "Confusing" ones to a human, along with a clear explanation of _why_ it's confused. This saves banks millions of dollars and prevents human error!

---

## 3. Delinquency Flags (The "Bad Track Record") 📉

In simple terms, a "Delinquency" happens when a person was supposed to pay a bill (like a credit card or a car loan) but **missed the deadline.**

### **What the specific flags mean:**

When you see these in the dropdown menu of our app, here is what they tell the bank:

- **30+ / 60+ / 90+ Days**: This tells us _how late_ the person was.
  - **30 Days**: They forgot or had a small delay (Common).
  - **90 Days**: They have a serious problem paying their bills (Very Risky).
- **Bankruptcy**: This is a legal status saying the person officially cannot pay back their debts. This is the biggest "Red Flag" possible in banking.
- **Charge-off**: This means a bank "gave up" on waiting for the person to pay and wrote the debt off as a loss. It means the person essentially "walked away" from their debt.

### **How the system uses them technically:**

The system looks at the **number** of flags you select:

- **0 flags**: Perfect score (1.0).
- **1 flag**: Subtracts **0.2** from the score (Minor Penalty).
- **2 or more flags**: Subtracts **0.35** from the score (Major Penalty).

**The Bottom Line:** These flags are the bank's way of asking: _"Can we trust this person to pay us back on time? Looking at their past, the answer is 'No' if these flags exist."_
