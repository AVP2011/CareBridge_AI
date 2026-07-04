# 🏥 CareBridge AI

<p align="center">
  <strong>AI-Powered Health Insurance Interpretation & Claim Support Platform</strong>
</p>

<p align="center">
Making health insurance understandable, transparent, and actionable for every policyholder.
</p>

<p align="center">

![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Gemma](https://img.shields.io/badge/Google-MedGemma-orange)
![License](https://img.shields.io/badge/License-MIT-success)

</p>

---

# 🎥 Project Preview

> **Demo Video**

https://github.com/AVP2011/CareBridge_AI/carebridge-ui/public/CareBridge-ui.png

---

# Overview

Health insurance should protect people during medical emergencies—not confuse them.

Unfortunately, policy documents are often lengthy, written in legal terminology, and difficult for most policyholders to understand. Many claims are rejected because consumers are unaware of exclusions, waiting periods, documentation requirements, or regulatory protections available to them.

**CareBridge AI** is designed to bridge this information gap.

Instead of simply summarizing a policy, it interprets insurance documents using a hybrid AI pipeline that combines medical reasoning, deterministic rule validation, and regulatory retrieval to generate practical, consumer-friendly guidance.

The platform helps users understand:

- what their policy actually covers
- potential risks before purchasing
- why a claim was rejected
- whether the rejection appears justified
- what steps can be taken next

---

# Why CareBridge AI?

Most insurance assistants today are essentially chatbot wrappers around an LLM.

CareBridge AI takes a different approach.

Instead of relying solely on generative AI, it combines multiple reasoning layers to improve reliability for insurance-related decisions.

The system includes:

- deterministic rule engines
- semantic document retrieval
- regulatory grounding using IRDAI publications
- medical reasoning
- structured report generation

The objective is not to replace professional legal or medical advice—but to help policyholders better understand their rights and available options.

---

# Core Features

## 📄 Pre-Purchase Policy Analysis

Analyze an insurance policy before purchasing it.

Features include:

- Waiting period analysis
- Hidden exclusions detection
- PED (Pre-existing Disease) evaluation
- Clause transparency assessment
- Consumer risk scoring
- Regulatory observations
- Policy strengths & weaknesses

---

## 🧾 Claim Rejection Audit

Upload a rejection letter together with the insurance policy.

CareBridge AI analyzes:

- rejection reason
- supporting policy clauses
- possible regulatory references
- appeal strength
- confidence level
- recommended next steps

---

## ⚖️ Policy Comparison

Compare two insurance policies side-by-side.

Comparison includes:

- Waiting periods
- PED coverage
- Co-payment
- Room rent restrictions
- Restoration benefits
- Day-care procedures
- Claim process
- Overall consumer friendliness

---

## 📚 Regulatory Guidance

Provides simplified explanations of official IRDAI regulations.

Includes:

- policyholder rights
- grievance process
- Ombudsman guidance
- Bima Bharosa information
- escalation workflow

---

# System Architecture

CareBridge AI follows a hybrid reasoning architecture designed specifically for high-risk document analysis.

```text
                  User Uploads Documents
                           │
                           ▼
                  Document Processing Layer
     ┌────────────────────────────────────────────┐
     │ PDF Extraction                             │
     │ OCR (Scanned Documents)                    │
     │ Document Cleaning                          │
     │ Intelligent Segmentation                   │
     └────────────────────────────────────────────┘
                           │
                           ▼
                Hybrid Clause Extraction Engine
     ┌────────────────────────────────────────────┐
     │ Tier 1 → Regex Extraction                  │
     │ Tier 2 → Semantic Retrieval                │
     │ Tier 3 → LLM Refinement                    │
     └────────────────────────────────────────────┘
                           │
                           ▼
                     Dual RAG Pipeline
     ┌────────────────────────────────────────────┐
     │ Standard Insurance Clauses                 │
     │ Official IRDAI Regulations                 │
     └────────────────────────────────────────────┘
                           │
                           ▼
               Hybrid Reasoning Engine
     ┌────────────────────────────────────────────┐
     │ MedGemma                                   │
     │ Gemini                                     │
     │ Rule Validation                            │
     └────────────────────────────────────────────┘
                           │
                           ▼
              Structured Consumer Report
```

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Framer Motion

## Backend

- FastAPI
- Python 3.11
- Uvicorn

## AI

- Google MedGemma
- Gemini
- Sentence Transformers
- FAISS

## OCR

- PaddleOCR
- Tesseract
- pdfplumber
- PyMuPDF
- OpenCV

---

# AI Pipeline

The inference pipeline consists of multiple validation stages.

```
Document Upload

↓

Text Extraction

↓

Document Segmentation

↓

Clause Extraction

↓

Semantic Retrieval

↓

IRDAI Compliance Matching

↓

Medical Reasoning

↓

Rule Validation

↓

Structured JSON Report

↓

Frontend Dashboard
```

---

# Project Structure

```
CareBridge_AI/

frontend/
backend/

backend/
├── api/
├── engines/
├── extractors/
├── rag/
├── rules/
├── prompts/
├── models/
├── services/
├── schemas/
├── tests/

docs/

README.md
SRS.md
```

---

# Running Locally

## Clone

```bash
git clone https://github.com/AVP2011/CareBridge_AI.git

cd CareBridge_AI
```

Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app:app --reload
```

Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# Current Modules

- ✅ Policy Analysis

- ✅ Claim Rejection Audit

- ✅ Clause Detection

- ✅ Regulatory Guidance

- ✅ Hybrid RAG

- 🚧 Agent Validation Engine

- 🚧 Smart Appeal Generator

- 🚧 Advanced Regulatory Intelligence

---

# Roadmap

### Phase 1

- Hybrid extraction engine
- Better OCR
- Dual FAISS index

### Phase 2

- Agent summary validation
- Regulatory compliance engine
- Industry benchmark comparison

### Phase 3

- Appeal letter generation
- Contradiction detection
- Risk benchmarking

### Phase 4

- Production deployment
- Performance optimization
- Real-world testing

---

# Project Status

CareBridge AI is currently under active development.

The current version focuses on building a reliable AI-assisted insurance interpretation system with emphasis on:

- extraction accuracy
- regulatory grounding
- explainable reasoning
- consumer-friendly outputs

---

# Disclaimer

CareBridge AI is an educational and research project.

The analysis generated by the system is intended to assist policyholders in understanding insurance documents and should not be considered legal, financial, or medical advice.

Users should consult qualified professionals before making decisions based on the generated reports.

---

# Author

### Aryan Vinay Pandey

Computer Engineering Student

AI • Machine Learning • Healthcare AI • Full Stack Development

GitHub

https://github.com/AVP2011

---

If you find this project useful, consider giving it a ⭐ on GitHub.

---

## 📜 Detailed Documentation
For a full technical breakdown, including functional requirements, API specifications, and data flow diagrams, refer to the [SRS Document](./SRS.md).
