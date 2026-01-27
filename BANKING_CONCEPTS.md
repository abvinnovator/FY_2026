# 🏦 Banking Concepts & System Guide

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

### **Delinquency Flags (Bad Track Record)** 📉

A "Delinquency" happens when a person was supposed to pay a bill but missed the deadline.

- **30/60/90 Days Late**: Tells the bank how long you delayed payment. 90 days is very serious.
- **Bankruptcy**: A legal status saying you cannot pay back debts. A major red flag.
- **Charge-off**: When a bank gives up on waiting for payment and takes a loss.

---

## 2. How the System Works (The "Three-Layer" Logic) ⚙️

Every time a credit application is submitted, our system follows three distinct steps:

### **Step 1: The Rule Check (The "Gatekeeper")**

Before the AI looks at the data, our code checks hardcoded rules. (e.g., "If DTI > 60%, flag it"). This is fast and transparent.

### **Step 2: The RAG Search (The "Library Search")** 📚

**RAG** stands for _Retrieval-Augmented Generation_.

1. The system looks at the application data.
2. It "searches" the `data/policies/` folder for relevant banking laws.
3. It finds the specific policy explaining why a certain DTI or Delinquency is risky.
4. It hands this text to the AI.

### **Step 3: The Gemini AI (The "Decision Expert")** 🧠

Now that Gemini has the **Math** and the **Rules**, it writes a human explanation.

- _Instead of:_ "Reject: Rule 4.4"
- _It says:_ "We are declining this because the applicant's DTI is 65%. This ensures the customer doesn't take on more debt than they can safely manage."

---

## 3. Why is this useful? 🚀

In the real world, a human loan officer can only review about 20-30 applications a day. Our system can review **thousands per second**.

It automatically identifies "Safe" apps and flags "Risky" ones with a clear AI-generated rationale. This helps banks make faster, fairer, and more explained decisions!
