"""
CareBridge AI — Dual RAG Builder
==================================
Builds two separate FAISS vector indices from the official IRDAI documents:

  INDEX 1: irdai_regulations
    - Health Insurance Regulations 2016
    - Standardization of Exclusions 2019
    - Protection of Policyholders 2017
    - Master Circular on Health Insurance 2024
    PURPOSE: Legal / compliance validation

  INDEX 2: standard_clauses
    - Curated benchmark clause definitions
    - Industry-standard PED, waiting period, sublimit norms
    PURPOSE: Compare uploaded policy vs. industry averages

Usage:
    python rag/rag_builder.py             # builds both indices
    python rag/rag_builder.py --index irdai   # rebuild only irdai index
    python rag/rag_builder.py --index clauses # rebuild only clause index
    python rag/rag_builder.py --test          # run retrieval smoke-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
RAG_DIR  = BASE_DIR

EMBED_MODEL = "multi-qa-MiniLM-L6-dot-v1"

# Chunking config
CHUNK_SIZE    = 800   # chars — enough for one regulatory paragraph
CHUNK_OVERLAP = 150

IRDAI_DOCS_DIR   = Path(__file__).parents[1] / "imp policies"
INDICES_DIR      = RAG_DIR / "indices"
REG_DOCS_DIR     = RAG_DIR / "regulatory_docs"

IRDAI_INDEX_PATH    = INDICES_DIR / "irdai_regulations.index"
IRDAI_MAP_PATH      = INDICES_DIR / "irdai_regulations_map.json"
CLAUSE_INDEX_PATH   = INDICES_DIR / "standard_clauses.index"
CLAUSE_MAP_PATH     = INDICES_DIR / "standard_clauses_map.json"

# ─── Source Documents ─────────────────────────────────────────────
# IRDAI source documents (file stems)
# ─────────────────────────────────────────────

IRDAI_PDF_FILES = [
    "Insurance Regulatory And Development Authority Of India (Health Insurance) Regulations, 2016.pdf",
    "Health Insurance IRDAI Ciruclar - Guidelines on standardization of exclusions in HI Contracts.pdf",
    "Insurance Regulatory And Development Authority of India (Protection of PolicyHolders' Interests) Regulations, 2017.pdf",
    "5. Master Circular on Health Insurance Business 2024.pdf",
]

# ─────────────────────────────────────────────
# Standard clause benchmark KB (inline)
# ─────────────────────────────────────────────

STANDARD_CLAUSE_KNOWLEDGE_BASE = """
## Waiting Period — Industry Standards
IRDAI mandates that the initial waiting period for any illness must not exceed 30 days from policy inception.
Pre-existing disease (PED) waiting periods vary between 12 and 48 months depending on the insurer.
As per IRDAI Master Circular 2016, after 8 years of continuous coverage, no claim can be denied on grounds of non-disclosure or pre-existing disease (Moratorium Rule).
Specific disease waiting periods (e.g., hernia, cataract, knee replacement) typically range from 24 to 48 months.

## Co-payment — Industry Standards
Co-payment clauses above 20% are considered consumer-unfriendly under IRDAI guidelines.
Senior citizen policies may carry co-payment of 10–30% depending on age at entry.
Policies with zero co-payment are rated more consumer-friendly.
Co-payment for non-network hospitals may be higher than for empanelled hospitals.

## Room Rent Sublimit — Industry Standards
Room rent limits below 1% of sum insured per day are considered restrictive.
A room rent limit of ₹5,000/day for a ₹5 lakh policy = 1% — borderline acceptable.
Proportionate deductions on room rent upgrades can significantly increase out-of-pocket costs.
Policies without room rent sublimits are considered more consumer-friendly.

## Pre-existing Disease (PED) — IRDAI Framework
PED is defined as any condition, ailment, or injury for which the insured had signs, symptoms, or was diagnosed within 48 months prior to policy issuance.
IRDAI circular dated 2019 standardizes the definition of pre-existing disease to prevent misuse by insurers.
Non-disclosure of PED at policy issuance: insurer can void the policy only within the first 3 years of coverage.
After 8 continuous years: Moratorium applies. No claim can be denied on grounds of PED or non-disclosure.

## Moratorium Rule — IRDAI Regulation 2016
Section 13 of IRDAI Health Insurance Regulations 2016: After 8 years of continuous renewal without claim, no insurer can reject a claim on grounds of non-disclosure or pre-existing disease.
Continuous coverage must be maintained without any gap year.
Even if policies are ported between insurers, the moratorium period carries forward as per IRDAI portability guidelines.

## Claim Settlement — IRDAI Mandates
Cashless claim: Insurer must give authorization within 1 hour of receiving complete documents (IRDAI Master Circular 2024).
Reimbursement claim: Insurer must settle within 30 days of receiving all documents.
Delay beyond 30 days triggers interest at 2% above bank rate per month.
Rejection of claim must be communicated in writing with specific policy clause cited.

## Exclusions — Standardized List (IRDAI 2019)
Standard exclusions under IRDAI Standardization of Exclusions 2019:
- Cosmetic or aesthetic treatment unless required for accident reconstruction
- Dental treatment (OPD) and vision correction (spectacles, contact lenses)
- Infertility and reproductive health treatments (unless explicitly covered)
- Obesity and weight management programs
- Hazardous sports and activities
- Self-inflicted injuries
- War or nuclear activities
- Non-allopathic treatments unless AYUSH rider is included

## Portability — IRDAI Circular
Policyholders have the right to port their policy to another insurer without losing waiting period credit.
Portability application must be made 45 days before renewal date.
Receiving insurer cannot impose fresh waiting periods for conditions already covered under the old policy.
PED waiting period credit carries forward in full.

## Grievance Redressal — IRDAI Framework
Step 1: Internal GRO (Grievance Redressal Officer) — 15-day response mandatory.
Step 2: Bima Bharosa (IRDAI integrated portal) — escalation after insurer non-response.
Step 3: Insurance Ombudsman — free, binding resolution for claims up to ₹50 lakhs.
Step 4: Consumer Forum / NCDRC — under Consumer Protection Act 2019.

## Free Look Period — IRDAI Rule
Minimum 15 days from policy receipt for the insured to review and return the policy.
Extended to 30 days for policies sold through distance marketing (online, telesales).
Premium is refunded minus proportionate risk premium and medical examination costs.

## Restoration Benefit — Policy Feature
Sum insured restoration reinstates the original coverage after exhaustion within the same policy year.
Some policies offer unlimited restoration; others restrict to one reinstatement per year.
Restoration is typically not applicable for the same illness that triggered the original claim.
"""


# ─────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-level chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if len(chunk) > 40:
            chunks.append(chunk)
        start += size - overlap
    return chunks


# ─────────────────────────────────────────────
# PDF text extraction (lightweight, no dep on extractors/)
# ─────────────────────────────────────────────

def _extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF for RAG indexing.
    Tries PyMuPDF → pdfplumber → raises if both fail.
    Does NOT use PaddleOCR here (RAG docs are digital, not scanned).
    """
    # Strategy 1: PyMuPDF
    try:
        import fitz
        parts = []
        with fitz.open(str(pdf_path)) as doc:
            for page in doc:
                parts.append(page.get_text("text"))
        text = "\n".join(parts)
        if len(text.strip()) > 200:
            print(f"    [PyMuPDF] [OK] {len(text):,} chars")
            return text
    except Exception as e:
        print(f"    [PyMuPDF] failed: {e}")

    # Strategy 2: pdfplumber
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                parts.append(t)
        text = "\n".join(parts)
        if len(text.strip()) > 200:
            print(f"    [pdfplumber] [OK] {len(text):,} chars")
            return text
    except Exception as e:
        print(f"    [pdfplumber] failed: {e}")

    raise RuntimeError(f"Could not extract text from: {pdf_path.name}")


# ─────────────────────────────────────────────
# Index builder
# ─────────────────────────────────────────────

def _build_faiss_index(
    chunks: list[str],
    embed_model,
    index_path: Path,
    map_path: Path,
    label: str,
) -> None:
    """Embed chunks and save a FAISS FlatL2 index + mapping JSON."""
    import faiss

    print(f"\n  [{label}] Embedding {len(chunks)} chunks...")
    t0 = time.time()
    embeddings = embed_model.encode(
        chunks,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    print(f"  [{label}] Embedding done in {time.time()-t0:.1f}s")

    # Normalize for stable L2 (effectively Cosine Similarity)
    faiss.normalize_L2(embeddings)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings, dtype=np.float32))

    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    map_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  [{label}] [OK] Saved index → {index_path.name} ({len(chunks)} chunks)")


# ─────────────────────────────────────────────
# Public build functions
# ─────────────────────────────────────────────

def build_irdai_index(embed_model) -> int:
    """
    Load all IRDAI regulatory PDFs, chunk, and build Index 1.
    Also loads any existing .txt files in rag/regulatory_docs/.
    Returns number of chunks indexed.
    """
    all_chunks: list[str] = []
    source_map: list[dict] = []  # track source per chunk for debugging

    # 1a. Load from official IRDAI PDFs
    for filename in IRDAI_PDF_FILES:
        pdf_path = IRDAI_DOCS_DIR / filename
        if not pdf_path.exists():
            print(f"  [WARN]  Not found: {filename} — skipping")
            continue
        print(f"\n  Loading: {filename[:70]}...")
        try:
            raw_text = _extract_pdf_text(pdf_path)
            chunks = _chunk_text(raw_text)
            all_chunks.extend(chunks)
            source_map.extend({"src": filename[:50], "idx": i} for i, _ in enumerate(chunks))
            print(f"  → {len(chunks)} chunks")
        except Exception as e:
            print(f"  [ERROR] Error: {e}")

    # 1b. Supplement with existing regulatory_docs .txt files
    if REG_DOCS_DIR.exists():
        for txt_file in sorted(REG_DOCS_DIR.glob("*.txt")):
            content = txt_file.read_text(encoding="utf-8", errors="ignore")
            chunks = _chunk_text(content)
            all_chunks.extend(chunks)
            print(f"  [txt] Loaded {len(chunks)} chunks from {txt_file.name}")

    if not all_chunks:
        print("  [ERROR] No IRDAI content found. Check imp policies/ directory.")
        return 0

    _build_faiss_index(all_chunks, embed_model, IRDAI_INDEX_PATH, IRDAI_MAP_PATH, "IRDAI")
    return len(all_chunks)


def build_standard_clause_index(embed_model) -> int:
    """
    Build Index 2 from the curated standard clause knowledge base.
    Returns number of chunks indexed.
    """
    chunks = _chunk_text(STANDARD_CLAUSE_KNOWLEDGE_BASE, size=400, overlap=60)
    print(f"\n  [Standard Clauses] {len(chunks)} chunks from knowledge base")
    _build_faiss_index(chunks, embed_model, CLAUSE_INDEX_PATH, CLAUSE_MAP_PATH, "Standard-Clauses")
    return len(chunks)


# ─────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────

def run_smoke_test():
    """Quick retrieval test on both indices after build."""
    from sentence_transformers import SentenceTransformer
    import faiss

    print("\n\n=== SMOKE TEST ===")
    model = SentenceTransformer(EMBED_MODEL)

    test_queries = [
        "pre-existing disease waiting period",
        "moratorium rule 8 years",
        "room rent sublimit proportionate deduction",
        "exclusion cosmetic treatment",
        "grievance ombudsman complaint",
    ]

    for index_path, map_path, label in [
        (IRDAI_INDEX_PATH,  IRDAI_MAP_PATH,  "IRDAI"),
        (CLAUSE_INDEX_PATH, CLAUSE_MAP_PATH, "Standard-Clauses"),
    ]:
        if not index_path.exists():
            print(f"  [{label}] index not found — run build first")
            continue

        index = faiss.read_index(str(index_path))
        chunks = json.loads(map_path.read_text(encoding="utf-8"))

        print(f"\n  [{label}] — {index.ntotal} vectors")
        for q in test_queries[:2]:
            qvec = model.encode([q])
            D, I = index.search(np.array(qvec, dtype=np.float32), 1)
            top_chunk = chunks[I[0][0]] if I[0][0] != -1 else "—"
            print(f"  Q: {q!r}")
            print(f"  A: {top_chunk[:120]}...")
            print()


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CareBridge RAG Index Builder")
    parser.add_argument("--index", choices=["irdai", "clauses", "all"], default="all",
                        help="Which index to build (default: all)")
    parser.add_argument("--test", action="store_true",
                        help="Run smoke test after building")
    args = parser.parse_args()

    print("="*60)
    print("CareBridge AI — RAG Index Builder")
    print("="*60)

    print("\nLoading sentence transformer...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    print("[OK] Model loaded")

    total_chunks = 0

    if args.index in ("irdai", "all"):
        print("\n--- Building IRDAI Regulations Index ---")
        total_chunks += build_irdai_index(model)

    if args.index in ("clauses", "all"):
        print("\n--- Building Standard Clause Index ---")
        total_chunks += build_standard_clause_index(model)

    print(f"\n[OK] Build complete — {total_chunks:,} total chunks indexed")

    if args.test:
        run_smoke_test()


if __name__ == "__main__":
    main()
