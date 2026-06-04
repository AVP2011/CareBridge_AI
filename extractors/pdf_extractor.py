"""
CareBridge AI — Production PDF Extractor
========================================
Strategy:
  1. PyMuPDF   → fast native text (best quality for digital PDFs)
  2. pdfplumber → layout-aware native text + table extraction
  3. PaddleOCR  → primary OCR (PRIMARY for scans, tables, photos)
  4. Tesseract  → fallback OCR (secondary for compatibility)

The extractor scores text quality after each attempt and stops
as soon as it receives usable output, avoiding unnecessary OCR calls.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# Quality scorer
# ─────────────────────────────────────────────

def _score_text(text: str) -> float:
    """
    Score extracted text quality (0.0 – 1.0).
    Uses three signals: length, word ratio, insurance keyword presence.
    """
    if not text or len(text.strip()) < 50:
        return 0.0

    words = text.split()
    if len(words) < 20:
        return 0.1

    # Ratio of normal alpha words
    alpha_ratio = sum(1 for w in words if w.isalpha()) / max(len(words), 1)

    # Insurance domain keywords boost score
    DOMAIN_KEYS = [
        "policy", "insured", "coverage", "premium", "claim",
        "exclusion", "waiting", "preexisting", "copay", "sublimit",
        "benefit", "deductible", "hospitalization", "irdai",
    ]
    text_lower = text.lower()
    keyword_hits = sum(1 for k in DOMAIN_KEYS if k in text_lower)
    keyword_boost = min(keyword_hits / 5, 0.3)

    score = (alpha_ratio * 0.7) + keyword_boost
    return min(score, 1.0)


# ─────────────────────────────────────────────
# Text cleaning
# ─────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Normalise and clean extracted text while preserving clause structure."""
    # Unicode normalisation
    text = unicodedata.normalize("NFKD", text)

    # Fix spaced-out characters (PDF artifact): "W a i t i n g" → "Waiting"
    text = re.sub(r"(?<=[a-zA-Z]) (?=[a-zA-Z] )", "", text)

    # Collapse 3+ blank lines into 2
    text = re.sub(r"[\r\n]{3,}", "\n\n", text)

    # Remove common page markers
    text = re.sub(r"[-–—]{3,}\s*Page\s*\d+\s*[-–—]{3,}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)

    # Strip lines
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


# ─────────────────────────────────────────────
# Extraction strategies
# ─────────────────────────────────────────────

def _try_pymupdf(pdf_path: str) -> Optional[str]:
    """Strategy 1 — PyMuPDF. Fast, high-fidelity for digital PDFs."""
    try:
        import fitz  # PyMuPDF
        parts = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                parts.append(page.get_text("text"))
        return "\n".join(parts)
    except ImportError:
        print("  [extractor] PyMuPDF not installed — skipping")
        return None
    except Exception as e:
        print(f"  [extractor] PyMuPDF failed: {e}")
        return None


def _try_pdfplumber(pdf_path: str) -> Optional[str]:
    """Strategy 2 — pdfplumber. Better for complex layouts + tables."""
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                parts.append(text)
                # Flatten tables into text
                for table in page.extract_tables() or []:
                    for row in table:
                        clean_row = [str(c).strip() if c else "" for c in row]
                        if any(clean_row):
                            parts.append(" | ".join(clean_row))
        return "\n".join(parts)
    except ImportError:
        print("  [extractor] pdfplumber not installed — skipping")
        return None
    except Exception as e:
        print(f"  [extractor] pdfplumber failed: {e}")
        return None


def _try_paddle_ocr(pdf_path: str) -> Optional[str]:
    """
    Strategy 3 — PaddleOCR (PRIMARY OCR).
    Converts PDF to images via PyMuPDF, then runs PaddleOCR.
    Handles scanned tables, tilted images, mixed layouts.
    """
    try:
        import fitz
        from paddleocr import PaddleOCR
        import numpy as np

        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

        parts = []
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc, 1):
                # Render at 200 DPI for OCR quality
                mat = fitz.Matrix(200 / 72, 200 / 72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, 3
                )
                result = ocr.ocr(img_array, cls=True)
                if result and result[0]:
                    lines = [line[1][0] for line in result[0] if line[1][0].strip()]
                    parts.append("\n".join(lines))

        return "\n".join(parts)
    except ImportError:
        print("  [extractor] PaddleOCR not installed — skipping")
        return None
    except Exception as e:
        print(f"  [extractor] PaddleOCR failed: {e}")
        return None


def _try_tesseract(pdf_path: str) -> Optional[str]:
    """
    Strategy 4 — Tesseract (FALLBACK OCR).
    Uses pdf2image to convert pages, then Tesseract for text.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path, dpi=250)
        parts = []
        for img in images:
            parts.append(pytesseract.image_to_string(img, lang="eng"))
        return "\n".join(parts)
    except ImportError:
        print("  [extractor] Tesseract / pdf2image not installed — skipping")
        return None
    except Exception as e:
        print(f"  [extractor] Tesseract failed: {e}")
        return None


# ─────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────

QUALITY_THRESHOLD = 0.35  # Minimum acceptable score to skip to next strategy


def extract_pdf(pdf_path: str) -> dict:
    """
    Extract text from a PDF using a waterfall of strategies.

    Returns:
        {
            "text": str,          # cleaned extracted text
            "method": str,        # strategy that succeeded
            "quality_score": float,
            "char_count": int,
        }

    Raises:
        FileNotFoundError: if path doesn't exist.
        RuntimeError: if all strategies fail.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    strategies = [
        ("pymupdf",    _try_pymupdf),
        ("pdfplumber", _try_pdfplumber),
        ("paddle_ocr", _try_paddle_ocr),
        ("tesseract",  _try_tesseract),
    ]

    best: dict | None = None

    for name, fn in strategies:
        print(f"  [extractor] Trying {name}...")
        raw = fn(str(path))
        if not raw:
            continue

        cleaned = _clean_text(raw)
        score = _score_text(cleaned)
        print(f"  [extractor] {name} → quality score {score:.2f} ({len(cleaned)} chars)")

        if best is None or score > best["quality_score"]:
            best = {
                "text": cleaned,
                "method": name,
                "quality_score": score,
                "char_count": len(cleaned),
            }

        # Good enough — stop here to avoid running slower OCR
        if score >= QUALITY_THRESHOLD and name in ("pymupdf", "pdfplumber"):
            print(f"  [extractor] ✅ Accepted {name} (score {score:.2f})")
            return best

    if best and best["quality_score"] > 0.0:
        print(f"  [extractor] ✅ Best result from {best['method']} (score {best['quality_score']:.2f})")
        return best

    raise RuntimeError(
        "All extraction strategies failed. "
        "PDF may be password-protected, corrupted, or empty."
    )


def extract_text_from_bytes(file_bytes: bytes, filename: str = "upload.pdf") -> dict:
    """
    Extract text from in-memory PDF bytes (for API file uploads).
    Writes to a temp file, extracts, then deletes.
    """
    import tempfile
    suffix = Path(filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return extract_pdf(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
