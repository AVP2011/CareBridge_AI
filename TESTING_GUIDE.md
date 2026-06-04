# 📖 CareBridge AI: Best-Case Testing Guide [v4.0]

This guide outlines the optimal workflow to verify the **Production-Grade Upgrade** we implemented.

---

## 🏗️ Phase 1: Engine Validation (Backend)
Run these automated scripts to ensure the "brains" of the system are functioning correctly before using the UI.

### 1. Hard Logic & Risk Engine
Verifies that the IRDAI rules and Broker Risk Engine can detect non-disclosure and missing citations.
```bash
python tests/logic_test.py
```
*   **Expected**: `✅ ALL DETERMINISTIC LOGIC TESTS PASSED`

### 2. RAG Retrieval (Normalized)
Confirms that the semantic search is correctly optimized for `multi-qa-MiniLM`.
```bash
python tests/rag_test.py
```
*   **Expected**: `✅ RAG Retrieval Verified.` (Retrieves 8-year moratorium data).

---

## 🎨 Phase 2: UI/UX & Professionalism
Verify the aesthetic upgrades and the new **Verdict-First** data flow.

### 1. Audit Report UI
1.  Start the app: `npm run dev` (already running).
2.  Navigate to the **Audit Page** (usually `/audit`).
3.  **Visual Check**:
    *   Confirm the new **Verdict Section** appears at the very top.
    *   Verify the **Risk Meter** (for Misrepresentation) is prominent with its high-end glassmorphism styling.
    *   Check for the **Institutional Typography** (Outfit sans-serif) in all headers.

### 2. Escalation & Support Page
1.  Navigate to the **Support Page** (usually `/support`).
2.  **Visual Check**:
    *   Verify the **Free Helplines** strip uses the new clean typography (no "funky" fonts).
    *   Test the **Ecosystem Tabs** (Official, Legal, NGO).
    *   Generate a **Draft Letter**: Fill out the form and ensure the copy/email buttons work with the updated professional styling.

---

## 🧪 Phase 3: The "Gold" Test Scenario
To see the system in its best light, perform a full end-to-end audit with this scenario:

### The "Diabetes Non-Disclosure" Case
*   **Policy Text**: `...Standard PED waiting period: 48 months. Non-disclosure of PED will void the claim...`
*   **Rejection Letter**: `...Claim rejected. We discovered you had diabetes since 2018 which was not declared. This is a violation of the PED clause...`
*   **Medical Documents**: `...Patient reports history of type-2 diabetes in 2018 records...`

**Expected Outcome**:
1.  **Extraction**: Correctly identifies the **PED Clause** and the **48-month period**.
2.  **Risk Engine**: Flags **High Risk** (0.7+) for Misrepresentation because the medical history (2018) predates the policy.
3.  **RAG**: Pulls in the **IRDAI 8-year moratorium rule** and **PED definition standardized 2019**.
4.  **UI**: Displays a "Critical Warning" verdict with a clear path to escalation via the updated Support Page.

---

> [!TIP]
> If you encounter any "ModuleNotFound" errors, ensure you are in the correct virtual environment and have run `pip install -r requirements.txt`.
