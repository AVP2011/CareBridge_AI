import re
from typing import Tuple

from services.document_classifier import DocumentClassifier

# ── Layer A: Mandatory Insurance Markers ───────────────────────────────────────
# At least MIN_MANDATORY of these must be present for the doc to be accepted.
MANDATORY_KEYWORDS = [
    r"sum insured",
    r"policy\s*(number|no\.?|schedule)",
    r"insurer",
    r"insured\s*(person|member)?",
    r"claim",
    r"benefit",
    r"exclusion",
    r"waiting period",
    r"premium",
    r"renewal",
]
MIN_MANDATORY = 4       # raised from 3 → 4

# ── Layer B: Strong Domain Markers ────────────────────────────────────────────
# At least MIN_STRONG of these MUST be present — these don't appear in
# any generic document (resume, timetable, etc.)
STRONG_KEYWORDS = [
    r"pre-existing disease",
    r"co-?payment",
    r"domiciliary",
    r"in-patient",
    r"hospitali[sz]ation",
    r"day care treatment",
    r"ayush",
    r"irdai",
    r"restoration benefit",
    r"room rent",
    r"network hospital",
    r"cashless",
    r"maternity benefit",
    r"ambulance",
]
MIN_STRONG = 2          # must match at least 2 strong domain terms

# ── Layer C: Hard Rejection Signals ───────────────────────────────────────────
# If ANY of these blocks is triggered, reject immediately.
HARD_REJECT_SIGNALS = {
    "Resume / CV": {
        "keywords": [r"curriculum vitae", r"work experience", r"career objective",
                     r"professional summary", r"references", r"linkedin\.com", r"hobbies"],
        "threshold": 2,
    },
    "Academic Document": {
        "keywords": [r"timetable", r"syllabus", r"semester", r"examination\s*(schedule|timetable|hall ticket)",
                     r"roll\s*number\b", r"class\s*teacher\b", r"lecture\s*hall\b"],
        "threshold": 2,
    },
    "Financial Statement": {
        "keywords": [r"profit and loss", r"balance sheet", r"gst number",
                     r"tax invoice", r"purchase order", r"invoice number"],
        "threshold": 2,
    },
}


_classifier = DocumentClassifier()   # singleton, avoid re-init on every call


def is_health_insurance_policy(text: str) -> Tuple[bool, str]:
    """
    4-Layer validation gate for CareBridge AI pre-purchase analysis.

    Layer 0 — Minimum length check
    Layer 1 — DocumentClassifier multi-class gate (with negative signal guard)
    Layer 2 — Hard reject signal override
    Layer 3 — Mandatory keyword threshold (≥ MIN_MANDATORY)
    Layer 4 — Strong domain keyword requirement (≥ MIN_STRONG)

    Returns:
        (True, reason)  →  proceed to analysis
        (False, reason) →  reject with user-friendly message
    """

    # ── Layer 0: Length ────────────────────────────────────────────────────────
    if not text or len(text.strip()) < 300:
        return False, (
            "The uploaded document is too short (less than 300 characters of readable text). "
            "Please upload the full Policy Wording PDF, not a summary or screenshot."
        )

    text_lower = text.lower()

    # ── Layer 1: DocumentClassifier ───────────────────────────────────────────
    result = _classifier.classify(text)

    # Immediate rejection for non-insurance classes
    if result.document_type == "NON_INSURANCE":
        neg = ", ".join(result.negative_signals[:4]) if result.negative_signals else "generic content"
        return False, (
            f"This document does not appear to be an insurance document "
            f"(detected signals: {neg}). "
            "Please upload a valid Health Insurance Policy Wording."
        )

    if result.document_type == "INSURANCE_BROCHURE":
        return False, (
            "This appears to be a Marketing Brochure or product leaflet, not a Policy document. "
            "Please upload the 'Policy Wording' or 'Policy Schedule' — usually a 30-100 page document "
            "provided by your insurer after purchase."
        )

    if result.document_type == "CLAIM_REJECTION":
        return False, (
            "This looks like a Claim Rejection / Repudiation Letter. "
            "Please use the 'Audit My Rejection' tool on CareBridge AI for this document."
        )

    if result.document_type == "MEDICAL_RECORD":
        return False, (
            "This is a Medical Record or Discharge Summary. "
            "CareBridge AI's Pre-Purchase analysis works only on Insurance Policy documents."
        )

    if result.document_type == "HOSPITAL_BILL":
        return False, (
            "This is a Hospital Bill / Invoice. "
            "CareBridge AI's Pre-Purchase analysis works only on Insurance Policy documents."
        )

    # ── Layer 2: Hard Reject Signal Override ──────────────────────────────────
    # Even if the classifier says HEALTH_POLICY, catch edge cases.
    for label, cfg in HARD_REJECT_SIGNALS.items():
        hits = [kw for kw in cfg["keywords"] if re.search(kw, text_lower)]
        if len(hits) >= cfg["threshold"]:
            return False, (
                f"Document classified tentatively as a policy, but it contains "
                f"strong signals of a '{label}' ({len(hits)} markers found: "
                f"{', '.join(hits[:3])}). Please upload an authentic Policy Wording."
            )

    # ── Layer 3: Mandatory Keyword Threshold ──────────────────────────────────
    mandatory_hits = [kw for kw in MANDATORY_KEYWORDS if re.search(kw, text_lower)]
    if len(mandatory_hits) < MIN_MANDATORY:
        missing = MIN_MANDATORY - len(mandatory_hits)
        return False, (
            f"Document is missing critical insurance markers "
            f"(found {len(mandatory_hits)}/{MIN_MANDATORY} required, need {missing} more). "
            "Ensure you have uploaded the complete Policy Wording and not just a cover page."
        )

    # ── Layer 4: Strong Domain Keyword Requirement ────────────────────────────
    strong_hits = [kw for kw in STRONG_KEYWORDS if re.search(kw, text_lower)]
    if len(strong_hits) < MIN_STRONG:
        return False, (
            f"Document lacks sufficient health-insurance-specific terminology "
            f"(found {len(strong_hits)}/{MIN_STRONG} required domain terms). "
            "Please upload a full Health Insurance Policy Wording (not a summary or certificate)."
        )

    # ── All layers passed ──────────────────────────────────────────────────────
    return True, (
        f"Valid health insurance policy confirmed "
        f"(classifier: {result.document_type} @ {result.confidence:.0%}, "
        f"mandatory markers: {len(mandatory_hits)}, "
        f"domain terms: {len(strong_hits)}, "
        f"structural signals: {len(result.metadata.get('structural_hits', []))})."
    )
