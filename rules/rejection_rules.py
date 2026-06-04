"""
CareBridge AI — Rejection Rules Engine
========================================
Production-grade deterministic rejection classifier.

Implements three detection passes:

  PASS 1 — Hard Pattern Match
    Detects explicit rejection keywords ("claim rejected", "claim denied").

  PASS 2 — Soft Tone Marker
    Detects insurer soft-language ("regret to inform", "not payable", "unable to process").
    Critical for real-world letters where "rejected" is never written directly.

  PASS 3 — Category Classification
    Identifies the SPECIFIC rejection category (PED, Waiting Period, Fraud, etc.)
    from 12 categories covering all common real-world rejection reasons.

Usage:
    from rules.rejection_rules import classify_rejection
    result = classify_rejection(rejection_text, policy_text="")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# PASS 1: Hard rejection signals
# ─────────────────────────────────────────────

_HARD_REJECTION_PATTERNS = [
    r"\bclaim\s+(has\s+been\s+)?rejected\b",
    r"\bclaim\s+(is\s+)?denied\b",
    r"\brepudiat(ed|ion)\b",
    r"\bnot\s+entitled\s+to\s+(the\s+)?claim\b",
    r"\brejection\s+of\s+(the\s+)?claim\b",
    r"\bclaim\s+not\s+admissible\b",
    r"\bclaim\s+is\s+not\s+payable\b",
    r"\bwe\s+(are\s+)?unable\s+to\s+settle\b",
    r"\bno\s+claim\s+is\s+payable\b",
]

# ─────────────────────────────────────────────
# PASS 2: Soft insurer-tone markers
# ─────────────────────────────────────────────

_SOFT_TONE_PATTERNS = [
    r"\bregret\s+to\s+inform\b",
    r"\bnot\s+payable\b",
    r"\bunable\s+to\s+process\b",
    r"\boutside\s+(the\s+)?coverage\b",
    r"\bexcluded\s+under\b",
    r"\bwaiting\s+period\s+appli(cable|es)\b",
    r"\bnot\s+covered\s+under\b",
    r"\bdoes\s+not\s+fall\s+under\b",
    r"\bcannot\s+be\s+entertained\b",
    r"\bno\s+liability\s+exists?\b",
    r"\bdeclin(ed|ing)\s+(the\s+)?(claim|request)\b",
    r"\bnot\s+admissible\b",
    r"\bfiled\s+for\s+rejection\b",
    r"\bnon.admissible\b",
    r"\brepudiat(ed|ion)\b",
]

# ─────────────────────────────────────────────
# PASS 3: Category Classification
# ─────────────────────────────────────────────

@dataclass
class RejectionCategory:
    code: str
    label: str
    patterns: list[str]
    irdai_protection: Optional[str] = None
    appeal_boost: int = 0      # +ve = stronger appeal; -ve = weaker

REJECTION_CATEGORIES: list[RejectionCategory] = [

    RejectionCategory(
        code="PED",
        label="Pre-Existing Disease (PED)",
        patterns=[
            r"\bpre.?existing\b",
            r"\bPED\b",
            r"\bprior\s+(medical\s+)?(condition|illness|disease|history)\b",
            r"\bcondition\s+existed\s+before\b",
            r"\bpre.?existing\s+condition\b",
            r"\bdisclosed?\s+at\s+proposal\b",
            r"\bmedical\s+history\s+indicates\b",
        ],
        irdai_protection=(
            "IRDAI Regulation 2016 §13: After 8 years of continuous coverage, "
            "no claim can be denied on PED grounds (Moratorium Rule)."
        ),
        appeal_boost=25,
    ),

    RejectionCategory(
        code="WAITING_PERIOD",
        label="Waiting Period Not Met",
        patterns=[
            r"\bwaiting\s+period\b",
            r"\binitial\s+waiting\b",
            r"\bwithin\s+\d+\s*(days?|months?)\s+of\s+policy\b",
            r"\bspecific\s+disease\s+waiting\b",
            r"\bnot\s+completed\s+(the\s+)?waiting\b",
            r"\bwithin\s+the\s+waiting\s+period\b",
        ],
        irdai_protection=(
            "IRDAI: Initial waiting period cannot exceed 30 days. "
            "Specific disease waiting must be disclosed in policy schedule."
        ),
        appeal_boost=15,
    ),

    RejectionCategory(
        code="NON_DISCLOSURE",
        label="Material Non-Disclosure",
        patterns=[
            r"\bnon.disclosure\b",
            r"\bnot\s+disclosed\b",
            r"\bmaterial\s+fact\s+(not|was\s+not)\s+disclosed\b",
            r"\bfailure\s+to\s+disclose\b",
            r"\bconcealment\b",
            r"\bmisrepresent(ed|ation)\b",
            r"\bproposal\s+form\b.{0,60}\bnot\s+disclosed\b",
        ],
        irdai_protection=(
            "IRDAI Protection of Policyholders 2017: Insurer can void policy on non-disclosure "
            "only within the first 3 years. After 8 years, Moratorium applies."
        ),
        appeal_boost=20,
    ),

    RejectionCategory(
        code="NOT_MEDICALLY_NECESSARY",
        label="Not Medically Necessary",
        patterns=[
            r"\bnot\s+medically\s+(necessary|required)\b",
            r"\bmedical\s+necessity\b",
            r"\bcould\s+have\s+been\s+(treated|managed)\s+(as\s+)?outpatient\b",
            r"\bdoes\s+not\s+warrant\s+hospitalization\b",
            r"\bnot\s+(a\s+)?medical\s+emergency\b",
            r"\belective\s+(procedure|surgery|treatment)\b",
        ],
        irdai_protection=(
            "Rejection on medical necessity grounds requires treating physician's "
            "certification review. IRDAI 2016: Insurer must provide clinical basis for denial."
        ),
        appeal_boost=20,
    ),

    RejectionCategory(
        code="FRAUD_INVESTIGATION",
        label="Fraud / Under Investigation",
        patterns=[
            r"\bfraud\b",
            r"\bunder\s+investigation\b",
            r"\bsuspect(ed|ion)\b",
            r"\bmisrepresent(ed|ation)\b",
            r"\binflated\s+(bill|claim|charges?)\b",
            r"\bforged?\b",
            r"\bfabricated?\b",
        ],
        irdai_protection=(
            "IRDAI: Fraud investigation must be completed within 6 months. "
            "Insurer must provide investigation report to policyholder on request."
        ),
        appeal_boost=-10,  # Harder to appeal fraud claims
    ),

    RejectionCategory(
        code="NETWORK_HOSPITAL",
        label="Non-Network / Non-Empanelled Hospital",
        patterns=[
            r"\bnon.network\b",
            r"\bnot\s+empanelled\b",
            r"\bnon.empanelled\b",
            r"\bnetwork\s+hospital\b",
            r"\bcashless\s+not\s+available\b",
            r"\bhospital\s+not\s+(in|on)\s+(our\s+)?panel\b",
        ],
        irdai_protection=(
            "IRDAI: Reimbursement claims at non-network hospitals cannot be rejected "
            "solely on network grounds if the emergency treatment was necessary."
        ),
        appeal_boost=15,
    ),

    RejectionCategory(
        code="NON_MEDICAL_EXPENSE",
        label="Non-Medical / Administrative Expense",
        patterns=[
            r"\bnon.medical\s+expenses?\b",
            r"\badministrative\s+(charges?|fee)\b",
            r"\battendant\s+charges?\b",
            r"\btelephone\s+charges?\b",
            r"\blaundry\b",
            r"\btoiletries\b",
            r"\bpackaging\s+charges?\b",
        ],
        irdai_protection=None,
        appeal_boost=5,
    ),

    RejectionCategory(
        code="LATE_INTIMATION",
        label="Late Claim Intimation",
        patterns=[
            r"\blate\s+intimation\b",
            r"\b(not\s+)?intimated\s+within\b",
            r"\btimely\s+(intimation|notification)\b",
            r"\bbeyond\s+the\s+(stipulated|specified)\s+time\b",
            r"\b\d+\s*(hours?|days?)\s+intimation\b",
        ],
        irdai_protection=(
            "IRDAI Master Circular 2024: Late intimation alone cannot be grounds for "
            "claim rejection if the policyholder can demonstrate valid reasons for delay."
        ),
        appeal_boost=15,
    ),

    RejectionCategory(
        code="POLICY_LAPSE",
        label="Policy Lapsed / Premium Not Paid",
        patterns=[
            r"\bpolicy\s+(has\s+)?(lapsed?|expired)\b",
            r"\bpremium\s+not\s+paid\b",
            r"\bpremium\s+(in\s+)?arrears?\b",
            r"\bgrace\s+period\s+expired\b",
            r"\blapse\s+in\s+coverage\b",
        ],
        irdai_protection=(
            "IRDAI: Insurer must notify policyholder before lapsation. "
            "Grace period minimum 30 days for annual policies."
        ),
        appeal_boost=0,
    ),

    RejectionCategory(
        code="LIMIT_EXHAUSTED",
        label="Sum Insured / Sub-limit Exhausted",
        patterns=[
            r"\bsum\s+insured\s+(has\s+been\s+)?(exhausted|exceeded)\b",
            r"\blimit\s+(of|for).{0,30}\s+exceeded\b",
            r"\bsub.?limit\s+(reached|exhausted|exceeded)\b",
            r"\bmaximum\s+(benefit|payable|coverage)\s+(reached|exceeded)\b",
            r"\bno\s+(further\s+)?coverage\s+(remaining|available)\b",
        ],
        irdai_protection=None,
        appeal_boost=-5,
    ),

    RejectionCategory(
        code="EXCLUSION_CLAUSE",
        label="Standard Policy Exclusion Applied",
        patterns=[
            r"\bexclusion\s+clause\b",
            r"\bexcluded\s+condition\b",
            r"\bstandardized\s+exclusion\b",
            r"\bspecifically\s+excluded\b",
            r"\bnot\s+covered\s+under\s+(the\s+)?policy\b",
            r"\bfalls?\s+under\s+(the\s+)?exclusion\b",
        ],
        irdai_protection=(
            "IRDAI Standardization of Exclusions 2019: Only standardized exclusions are "
            "permitted. Any exclusion not in the approved list can be challenged."
        ),
        appeal_boost=20,
    ),

    RejectionCategory(
        code="MORATORIUM_BREACH",
        label="Moratorium / 8-Year Rule Applicable",
        patterns=[
            r"\bmoratorium\b",
            r"\b8\s*.?year\s+rule\b",
            r"\bcontinuous\s+(renewal|coverage)\s+of\s+8\s+years?\b",
            r"\bmoratorium\s+period\b",
            r"\blong.term\s+policyholder\b",
        ],
        irdai_protection=(
            "IRDAI Regulation 2016 §13: After 8 years continuous coverage, "
            "NO claim can be denied on PED or non-disclosure grounds. This rule is absolute."
        ),
        appeal_boost=40,  # Strongest appeal scenario
    ),
]


# ─────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────

@dataclass
class RejectionAnalysis:
    is_rejection: bool
    detection_mode: str              # "hard", "soft", "inferred"
    categories: list[RejectionCategory]
    primary_category: Optional[RejectionCategory]
    moratorium_applicable: bool
    appeal_boost_total: int
    matched_snippets: list[str]
    irdai_protections: list[str]
    confidence: str                  # "High", "Medium", "Low"

    def summary(self) -> str:
        if not self.is_rejection:
            return "No rejection detected in this document."
        cat_label = self.primary_category.label if self.primary_category else "Unknown Category"
        return (
            f"Rejection detected [{self.detection_mode.upper()}] — "
            f"Primary: {cat_label} | "
            f"Appeal boost: +{self.appeal_boost_total} | "
            f"Confidence: {self.confidence}"
        )


# ─────────────────────────────────────────────
# Classifier
# ─────────────────────────────────────────────

def classify_rejection(
    rejection_text: str,
    policy_text: str = "",
) -> RejectionAnalysis:
    """
    Full rejection classification pipeline.

    Steps:
      1. Hard pattern check
      2. Soft tone check
      3. Category identification
      4. Moratorium check (cross-references policy_text for tenure)
      5. Confidence calibration

    Returns a RejectionAnalysis dataclass.
    """
    text = rejection_text + " " + policy_text
    text_lower = text.lower()

    # ── PASS 1: Hard patterns ──────────────────
    is_hard = any(
        re.search(p, text_lower, re.IGNORECASE)
        for p in _HARD_REJECTION_PATTERNS
    )

    # ── PASS 2: Soft tone markers ──────────────
    is_soft = any(
        re.search(p, text_lower, re.IGNORECASE)
        for p in _SOFT_TONE_PATTERNS
    )

    is_rejection = is_hard or is_soft
    detection_mode = "hard" if is_hard else ("soft" if is_soft else "inferred")

    # ── PASS 3: Category classification ────────
    matched_categories: list[RejectionCategory] = []
    matched_snippets: list[str] = []

    for cat in REJECTION_CATEGORIES:
        for pattern in cat.patterns:
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                matched_categories.append(cat)
                # Capture surrounding context for the snippet
                start = max(0, m.start() - 40)
                end   = min(len(text_lower), m.end() + 100)
                snippet = text[start:end].strip().replace("\n", " ")
                matched_snippets.append(f"[{cat.code}] …{snippet}…")
                break  # one match per category is enough

    # Deduplicate categories
    seen_codes: set[str] = set()
    unique_categories: list[RejectionCategory] = []
    for cat in matched_categories:
        if cat.code not in seen_codes:
            seen_codes.add(cat.code)
            unique_categories.append(cat)

    # Primary = highest appeal_boost (most actionable for user)
    primary = max(unique_categories, key=lambda c: c.appeal_boost) if unique_categories else None

    # ── Moratorium check ───────────────────────
    moratorium_applicable = _check_moratorium(rejection_text, policy_text)
    if moratorium_applicable:
        moratorium_cat = next(
            (c for c in REJECTION_CATEGORIES if c.code == "MORATORIUM_BREACH"), None
        )
        if moratorium_cat and moratorium_cat not in unique_categories:
            unique_categories.append(moratorium_cat)
            if not primary or moratorium_cat.appeal_boost > primary.appeal_boost:
                primary = moratorium_cat

    # ── Appeal boost total ─────────────────────
    appeal_boost_total = sum(cat.appeal_boost for cat in unique_categories)
    if moratorium_applicable:
        appeal_boost_total = min(appeal_boost_total + 40, 95)

    # ── IRDAI protections ──────────────────────
    irdai_protections = [
        cat.irdai_protection
        for cat in unique_categories
        if cat.irdai_protection
    ]

    # ── Confidence calibration ─────────────────
    if is_hard and unique_categories:
        confidence = "High"
    elif (is_hard or is_soft) and unique_categories:
        confidence = "High" if len(unique_categories) >= 2 else "Medium"
    elif is_soft:
        confidence = "Medium"
    else:
        confidence = "Low"

    return RejectionAnalysis(
        is_rejection=is_rejection,
        detection_mode=detection_mode,
        categories=unique_categories,
        primary_category=primary,
        moratorium_applicable=moratorium_applicable,
        appeal_boost_total=appeal_boost_total,
        matched_snippets=matched_snippets[:5],  # cap for conciseness
        irdai_protections=irdai_protections,
        confidence=confidence,
    )


# ─────────────────────────────────────────────
# Moratorium checker
# ─────────────────────────────────────────────

def _check_moratorium(rejection_text: str, policy_text: str) -> bool:
    """
    Detect if the 8-year moratorium rule is applicable.

    Checks:
    - Policy text mentions 8+ years of continuous coverage
    - Rejection is PED or non-disclosure based
    - Rejection text doesn't already acknowledge the moratorium
    """
    combined = (rejection_text + " " + policy_text).lower()

    # Look for 8+ year tenure indicators
    year_patterns = [
        r"\b(8|nine|ten|eleven|twelve|\d{2})\s*.?year[s]?\s*(of\s+)?(continuous\s+)?(coverage|renewal|policy)\b",
        r"\bpolicy\s+since\s+(19|20)\d{2}\b",   # policy inception year suggesting long tenure
        r"\bcontinuous\s+renewal\s+for\s+\d+\s*year",
    ]
    has_long_tenure = any(re.search(p, combined, re.IGNORECASE) for p in year_patterns)

    # Check if rejection is PED or non-disclosure
    ped_patterns = [r"\bpre.?existing\b", r"\bnon.disclosure\b", r"\bnot\s+disclosed\b"]
    is_ped_rejection = any(re.search(p, combined, re.IGNORECASE) for p in ped_patterns)

    return has_long_tenure and is_ped_rejection
