# 🏦 Intelligent Banking Operations Agent: User Guide

Welcome! This project is a demonstration of how **Artificial Intelligence** can be used to automate and assist in critical banking decisions, specifically **Fraud Detection** and **Credit Risk Assessment**.

---

## 1. What is this project about? 🤖

The goal of this project is to create a "Digital Assistant" for bank employees. Instead of a human having to manually check every single transaction or loan application, our AI agents do the "heavy lifting."

- **Fraud Triage Agent**: Acts like a digital detective. It looks at transactions in real-time and flags them if they look suspicious.
- **Credit Risk Agent**: Acts like a digital loan officer. It evaluates whether a person can afford a loan based on their income and debts.

---

## 2. Where is the AI (Gemini) used? 🧠

The "Intelligence" in this project comes in two layers:

1.  **Fast Layer (Non-AI)**: For speed, we use standard math and rules. This is always on.
2.  **Smart Layer (AI/Gemini)**: This is used for **Reasoning**. I have updated the code to use **Google Gemini 1.5 Flash**!

### **How to see the AI in action:**

1.  **Add your Key**: Open the `.env` file in the root directory and replace `your_google_api_key_here` with your actual **Google AI API Key**.
2.  **Run a Triage**: Submit a transaction in the "Fraud Triage" or "Credit Triage" pages.
3.  **Check the "Rationale"**:
    - **Without a Key**: You will see a message saying the AI reasoning is disabled.
    - **With a Key**: The AI (Gemini) will write a **dynamic, professional explanation** tailored to the specific data you entered!
    - **Default Explanations**: I have commented out the repetitive hardcoded explanations as requested, so now you only see the high-quality AI rationale.

---

## 3. Understanding the Input Fields 📝

### **Fraud Triage (The Detective)**

| Field         | Meaning                              | Why it matters                                                                            |
| :------------ | :----------------------------------- | :---------------------------------------------------------------------------------------- |
| **Amount**    | The cost of the transaction.         | High amounts usually trigger more security checks.                                        |
| **MCC**       | Merchant Category Code (e.g., 7995). | Some codes (like 7995 for Gambling) are higher risk than others.                          |
| **Geo**       | The location (e.g., US-NY).          | If you usually shop in London and suddenly appear in New York, it's a "Geo-Novelty" flag. |
| **Device ID** | Unique ID for the phone/laptop.      | Fraudsters often use new, unrecognized devices.                                           |
| **Channel**   | ecommerce, pos, atm, etc.            | Online (ecommerce) shopping is generally riskier than in-person (pos).                    |

### **Credit Triage (The Loan Officer)**

| Field                 | Meaning                                   |
| :-------------------- | :---------------------------------------- |
| **Income**            | How much the person earns per month.      |
| **Liabilities**       | How much they already owe (monthly debt). |
| **Requested Limit**   | How much of a credit line they want.      |
| **Delinquency Flags** | History of missed payments.               |

---

## 4. How to Test (Scenario Ideas) 🧪

Try these inputs instead of the defaults to see the agents in action:

### **Test Scenario A: "The High-Risk Fraudster"**

- **Amount**: `5000` (Sudden large spike)
- **MCC**: `7995` (Gambling/High Risk)
- **Geo**: `RU-MOS` (New location far away)
- **Device ID**: `dev-unknown-999` (New device)
- **Result**: You should see a **HIGH RISK** alert with a detailed rationale.

### **Test Scenario B: "The Unaffordable Loan"**

- **Income**: `2000`
- **Liabilities**: `1800` (This makes the **DTI** 90%)
- **Requested Limit**: `10000`
- **Result**: The "Credit Triage" should **Reject** or flag for manual review because the Debt-to-Income (DTI) ratio is too high.

---

## 5. Summary of Use Case 💡

In a real bank, this system helps **scale operations**. A single person can monitor thousands of accounts because the AI only surfaces the most suspicious 1% of cases for human review, while automatically approving 99% of safe transactions.

**Now, go to your Browser dashboard and try entering these "High Risk" scenarios to see how the system alerts you!**
