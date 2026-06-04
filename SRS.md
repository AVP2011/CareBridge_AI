# Software Requirements Specification (SRS)
# CareBridge AI — AI-Powered Health Insurance Interpretation & Escalation Support Platform

---

| Field | Details |
|-------|---------|
| **Document Version** | v3.0.0 (Production Grade Upgrade) |
| **Project Name** | CareBridge AI |
| **Prepared By** | Aryan Vinay Pandey |
| **Date** | June 2026 |
| **Status** | Final / Production Ready |
| **Classification** | Internal / Public Release |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Functional Requirements (Upgraded)](#4-functional-requirements-upgraded)
5. [AI & ML Logic (The Rule Engine Upgrade)](#5-ai--ml-logic-the-rule-engine-upgrade)
6. [Design & UI/UX Standards](#6-design--uiux-standards)
7. [External Interface & API](#7-external-interface--api)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Documentation & Export Modules](#9-documentation--export-modules)
10. [Glossary](#10-glossary)

---

## 1. Introduction

### 1.1 Purpose
This document defines the high-level and detailed requirements for **CareBridge AI**, an upgraded, production-grade intelligence platform designed to decode the complexity of health insurance. The system serves as a "regulatory co-pilot" for Indian policyholders, translating dense legal terms into actionable insights.

### 1.2 Scope (The v3.0 Upgrade)
CareBridge AI has been transformed from a prototype into a robust ecosystem:
- **Next.js Frontend:** A premium, editorial-style interface optimized for clarity and rapid document digestion.
- **FastAPI Advanced Backend:** Hosting a dual-pass inference engine that combines LLM reasoning with deterministic rule overrides.
- **Enhanced Rejection Logic:** Support for 12 real-world rejection patterns (e.g., fraud, medical necessity, 8-year moratorium).
- **OCR Multi-Step Pipeline:** Tesseract-powered fallback for scanned letters and medical documents.
- **Escalation Intelligence:** Directly linked to verified regulatory portals (Bima Bharosa, NCDRC).

### 1.3 Problem Statement
The "legibility gap" in Indian health insurance leads to massive financial loss. Consumers purchase policies based on marketing brochures but are rejected based on fine-print exclusions. When rejected, they lack the tools to verify if the rejection is lawful or how to approach the Ombudsman.

---

## 2. Overall Description

### 2.1 Product Perspective
CareBridge AI is a standalone, privacy-first platform. It follows a "Stateless Analysis" model—no health or policy data is stored after the analysis session concludes.

### 2.2 Core Modules
1. **Pre-Purchase Analyzer:** Risk-scores policies across 10 categories (PED, Sub-limits, Waiting Periods).
2. **Audit Rejection Engine:** A 12-rule classifier that compares rejection letters against policy terms.
3. **Smart Comparison:** Parallel analysis of two policies to identify the "safer" choice.
4. **Interactive Report Chat:** Context-aware Q&A based on the generated audit/analysis.
5. **Regulatory Support Hub:** Compact, verified escalation paths for IRDAI, Ombudsman, and Legal Aid.

---

## 3. System Architecture Overview

### 3.1 The Hybrid Intelligence Layer
- **LLM Core:** Google Gemma-2 2B / Gemini models for contextual interpretation.
- **Pass 1 (Tone Marker):** Detects "Insurer Soft-Language" (e.g., "not admissible", "regret to inform") to flag rejection sentiment even if keywords are missing.
- **Pass 2 (Rule Classifier):** Deterministic regex-based extraction of 12 rejection categories and 10 policy risks.
- **RAG Tier:** `sentence-transformers` for retrieval of IRDAI circulars and standard insurance clauses.

---

## 4. Functional Requirements (Upgraded)

### 4.1 Claim Rejection Audit (Production-Grade)
- **OCR Logic:** Seamlessly handles photos/scans of rejection letters using Tesseract version-fallback.
- **12 Rejection Scenarios:** 
  - Pre-Existing Disease (PED), Non-Disclosure, Waiting Period, Not Medically Necessary, Fraud/Investigation, Network/Non-PPH, Non-Medical Expenses, Late Intimation, Policy Lapse, Limit Exhausted, Ambiguous Clause, and Moratorium Breach (8-Year Rule).
- **Confidence Calibration:** Returns "High/Medium/Low" confidence based on text quality and rule-match density.

### 4.2 Support & Help Portal (Redesign)
- **Consolidated View:** Replaced cluttered grid with an **interactive accordion layout**.
- **Verified Escalation:** Direct integration of the modernized **Bima Bharosa Portal** (formerly IGMS) and **NCDRC** (Consumer Forum) links.
- **Timelined Guidance:** Clearly states 15-day GRO windows and 1-year Ombudsman limits.

### 4.3 Policy Comparison UI
- **Professional Metrics Panel:** A dedicated side-panel showing "Live Analysis Metrics" (Clause categories, IRDAI markers, Model parameters).

---

## 5. AI & ML Logic (The Rule Engine Upgrade)

### 5.1 Secondary Pass: The Tone Marker
To prevent false-negative analyses, the system now implements a **Secondary Tone Marker Pass**. If the rule engine doesn't find a hard keyword (e.g., "rejected"), it scans for "Insurer Tone" (e.g., "regret to inform", "filed for rejection", "not eligible for claim"). This ensures the LLM always knows the context of the document.

### 5.2 Document Truncation (Smart Sampling)
Handles policies up to 100 pages by sampling the preamble (definitions), the mid-section (exclusions), and the end (grievance process), ensuring context is never lost.

---

## 6. Design & UI/UX Standards

### 6.1 The "Editorial" Aesthetic
The UI has been upgraded to a premium, product-grade design system:
- **Typography:** DM Mono (for data), Cormorant Garamond (for titles), and Outfit (for metrics).
- **Summary-First Navigation:** Interactive audit reports that prioritize "Summary & Appeal Strength" before diving into technical clauses.
- **Sample Selection:** Replaced "childish" pills with a **Professional Editorial Table** showing real-world case scenarios for user onboarding.
- **Visual Feedback:** Glassmorphism headers, subtle micro-animations (SFX-inspired), and a clean "Document-Style" card layout.

---

## 7. External Interface & API

### 7.1 Frontend-Backend Bridge
- **Centralized API (`api.ts`):** Unified communication layer with typing for all analysis reports.
- **Multipart Form Support:** robust handling of PDF/Image uploads with progress tracking.

---

## 8. Non-Functional Requirements

### 8.1 Safety & Ethics
- **AI Footnote:** A persistent "Interpretative Analysis Only" footer on all reports, emphasizing non-legal status.
- **Performance:** Analysis completion within < 15 seconds for text and < 45 seconds for OCR-heavy PDF scans.

---

## 9. Documentation & Export Modules

### 9.1 Presentation Generation
- **Automated PPTX Module:** Ability to generate high-level 8-slide summary decks (`CareBridge_Pitch_Deck.pptx`) summarizing the analysis for external review.

---

## 10. Glossary
- **Bima Bharosa:** The modernized IRDAI grievance portal.
- **PED:** Pre-Existing Disease (The #1 cause of rejection).
- **Moratorium Rule:** IRDAI rule prohibiting rejection after 8 continuous years of coverage.
- **NCDRC:** National Consumer Disputes Redressal Commission.

---
*Last Updated: May 2026*
*CareBridge AI — Making Insurance Legible.*
