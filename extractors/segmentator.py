"""
CareBridge AI — Document Segmentator
======================================
Splits insurance documents into labelled sections BEFORE passing
to extraction or LLM, so:
  - The LLM only ever sees the relevant section
  - Extraction patterns run on a pre-filtered slice
  - Confidence of extraction improves significantly

Sections detected:
  DEFINITIONS, WAITING_PERIOD, EXCLUSIONS, PED,
  COPAYMENT, ROOM_RENT, CLAIM_PROCEDURE,
  GRIEVANCE, MATERNITY, RESTORATION, NETWORK,
  FREE_LOOK, GENERAL (catch-all)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
# Section registry
# ─────────────────────────────────────────────

SECTION_PATTERNS: dict[str, list[str]] = {
    "DEFINITIONS": [
        r"\bdefinitions?\b",
        r"\binterpretations?\b",
        r"\bmeaning of terms\b",
    ],
    "WAITING_PERIOD": [
        r"\bwaiting period\b",
        r"\binitial waiting\b",
        r"\bmoratorium\b",
        r"\bspecific disease waiting\b",
    ],
    "PED": [
        r"\bpre.?existing\b",
        r"\bPED\b",
        r"\bprior illness\b",
        r"\bdiseases? existing\b",
    ],
    "EXCLUSIONS": [
        r"\bexclusions?\b",
        r"\bnot covered\b",
        r"\bwhat is not covered\b",
        r"\bexcluded conditions?\b",
        r"\bpermanent exclusions?\b",
        r"\bgeneral exclusions?\b",
    ],
    "COPAYMENT": [
        r"\bco.?pay(ment)?\b",
        r"\bpolicyholder.s contribution\b",
        r"\binsured.s share\b",
    ],
    "ROOM_RENT": [
        r"\broom.rent\b",
        r"\broom charges?\b",
        r"\baccommodation (limit|charges?)\b",
        r"\bward type\b",
    ],
    "CLAIM_PROCEDURE": [
        r"\bclaim (procedure|process|intimation)\b",
        r"\bhow to (file|make|register) a claim\b",
        r"\bcashless (procedure|process|claim)\b",
        r"\breimbursement (procedure|process)\b",
    ],
    "GRIEVANCE": [
        r"\bgrievance (redressal|mechanism|process)\b",
        r"\bcomplaint\b",
        r"\bombudsman\b",
        r"\bescalation\b",
    ],
    "MATERNITY": [
        r"\bmaternity\b",
        r"\bnewborn\b",
        r"\bdelivery (benefit|charges?)\b",
    ],
    "RESTORATION": [
        r"\brestoration\b",
        r"\brecharge\b",
        r"\bsum insured restoration\b",
        r"\breinstatement\b",
    ],
    "NETWORK": [
        r"\bnetwork hospital\b",
        r"\bcashless hospital\b",
        r"\bempanelled hospital\b",
    ],
    "FREE_LOOK": [
        r"\bfree look\b",
        r"\bfree.?look period\b",
        r"\bcooling.off\b",
    ],
    "SUBLIMIT": [
        r"\bsub.?limit\b",
        r"\bcapping\b",
        r"\bmaximum payable\b",
        r"\bdisease.wise limit\b",
    ],
}

# Compile once for performance
_COMPILED: dict[str, list[re.Pattern]] = {
    section: [re.compile(p, re.IGNORECASE) for p in patterns]
    for section, patterns in SECTION_PATTERNS.items()
}


# ─────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────

@dataclass
class DocumentSection:
    label: str              # e.g. "EXCLUSIONS"
    text: str               # raw text of this section
    start_char: int = 0
    end_char: int = 0
    confidence: float = 1.0


@dataclass
class SegmentedDocument:
    sections: dict[str, DocumentSection] = field(default_factory=dict)
    general_text: str = ""  # everything not matched to a section

    def get(self, section: str, default: str = "") -> str:
        """Return text for a section or default."""
        sec = self.sections.get(section)
        return sec.text if sec else default

    def priority_text(
        self,
        sections: list[str],
        max_chars: int = 8000,
    ) -> str:
        """
        Return a concatenated text block from listed sections.
        Used to feed focused context to the LLM.
        """
        parts = []
        total = 0
        for label in sections:
            if label in self.sections:
                chunk = f"\n\n[{label}]\n" + self.sections[label].text
                parts.append(chunk)
                total += len(chunk)
                if total >= max_chars:
                    break
        return "\n".join(parts) if parts else self.general_text[:max_chars]

    def to_dict(self) -> dict:
        return {
            label: {"text": sec.text[:500], "confidence": sec.confidence}
            for label, sec in self.sections.items()
        }


# ─────────────────────────────────────────────
# Segmentation logic
# ─────────────────────────────────────────────

def _find_header_spans(text: str) -> list[tuple[int, int, str]]:
    """
    Find candidate section header positions in the document.
    Returns list of (start, end, label).

    Strategy:
    - Split on double newlines (paragraph breaks)
    - Score each paragraph's first line against section patterns
    - A paragraph is a header if it: is short (<= 120 chars), 
      starts with a capital, and matches a pattern
    """
    spans: list[tuple[int, int, str]] = []
    paragraphs = re.split(r"\n{2,}", text)
    cursor = 0

    for para in paragraphs:
        para_start = text.find(para, cursor)
        if para_start == -1:
            cursor += len(para)
            continue

        first_line = para.split("\n")[0].strip()

        if 3 < len(first_line) <= 120:
            for label, patterns in _COMPILED.items():
                if any(p.search(first_line) for p in patterns):
                    spans.append((para_start, para_start + len(first_line), label))
                    break

        cursor = para_start + len(para)

    return spans


def segment_document(text: str) -> SegmentedDocument:
    """
    Split a raw insurance document text into labelled sections.

    Returns a SegmentedDocument with per-section text that can be
    queried by label for targeted extraction.
    """
    result = SegmentedDocument()
    spans = _find_header_spans(text)

    if not spans:
        # No structure found — return entire doc as general
        result.general_text = text
        return result

    # Build section slices between detected headers
    for i, (start, end, label) in enumerate(spans):
        next_start = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        section_text = text[end:next_start].strip()

        if label in result.sections:
            # Append if section seen twice (e.g., multiple exclusion lists)
            result.sections[label].text += "\n" + section_text
        else:
            result.sections[label] = DocumentSection(
                label=label,
                text=section_text,
                start_char=start,
                end_char=next_start,
                confidence=0.9,
            )

    # Text before first header = general preamble
    if spans:
        result.general_text = text[: spans[0][0]].strip()

    return result


def segment_for_rejection_audit(
    rejection_text: str,
    policy_text: Optional[str] = None,
) -> tuple[SegmentedDocument, SegmentedDocument | None]:
    """
    Convenience wrapper for the rejection audit pipeline.
    Segments both rejection letter and policy independently.
    """
    rejection_doc = segment_document(rejection_text)
    policy_doc = segment_document(policy_text) if policy_text else None
    return rejection_doc, policy_doc
