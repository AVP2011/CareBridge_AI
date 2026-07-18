import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ClassificationResult(BaseModel):
    """Result of classifying a document."""
    document_type: str
    confidence: float
    reasoning: str
    validation_score: float = 0.0       # 0.0 → 1.0 composite score
    negative_signals: List[str] = []    # flags that caused rejection
    metadata: Dict[str, Any] = {}


class DocumentClassifier:
    """
    Production-grade multi-layer document classifier for CareBridge AI.

    Layers:
      1. Negative Signal Guard  — block hard non-insurance docs (CV, timetable, recipe…)
      2. Multi-Class Scoring    — weighted keyword density per document class
      3. Structural Pattern Check — policy number, IRDAI reg, date patterns
      4. Composite Confidence   — combined signal → final label + score
    """

    # ── 1. NEGATIVE SIGNAL LIBRARY ─────────────────────────────────────────────
    # Documents that contain ≥ NEGATIVE_THRESHOLD of these tags are REJECTED
    # immediately as NON_INSURANCE, regardless of other scores.
    NEGATIVE_SIGNALS = {
        "RESUME_CV": {
            "keywords": [
                r"\bcurriculum vitae\b", r"\bresume\b", r"\bwork experience\b",
                r"\bskills\b", r"\bobjective\b", r"\beducation\b", r"\bgpa\b",
                r"\binternship\b", r"\breferees?\b", r"\blinkedin\.com\b",
                r"\bprofessional summary\b", r"\bcareer objective\b",
                r"\bhobbies\b", r"\bprojects\b", r"\bcertifications\b",
                r"\bachievements\b", r"\b(b\.?tech|m\.?tech|b\.?e\.?|mba|bsc|bca)\b",
            ],
            "threshold": 3,     # ≥3 hits → labelled as RESUME
        },
        "ACADEMIC": {
            "keywords": [
                r"\btimetable\b", r"\bschedule of classes\b", r"\bsyllabus\b",
                r"\bsemester\b", r"\bexamination\b", r"\bmarks\b",
                r"\buniversity\b", r"\bcollege\b", r"\bstudent\b",
                r"\broll number\b", r"\bassignment\b", r"\blecture\b",
                r"\bperiod\b.*\bsubject\b", r"\bteacher\b", r"\bprincipal\b",
            ],
            "threshold": 3,
        },
        "RECIPE_FOOD": {
            "keywords": [
                r"\brecipe\b", r"\bingredients?\b", r"\bteaspoon\b",
                r"\btablespoon\b", r"\bbake\b", r"\bcook\b",
                r"\boven\b", r"\bflour\b", r"\bsugar\b",
            ],
            "threshold": 3,
        },
        "LEGAL_CONTRACT": {
            "keywords": [
                r"\bagreement between\b", r"\bhereinafter referred\b",
                r"\bparty of the first\b", r"\bwhereas\b",
                r"\bterms and conditions\b.*\bsoftware\b",
                r"\blicensee\b", r"\bsource code\b",
            ],
            "threshold": 2,
        },
        "FINANCIAL_GENERIC": {
            "keywords": [
                r"\bprofit and loss\b", r"\bbalance sheet\b",
                r"\bstock market\b", r"\bshare price\b",
                r"\bdividend\b", r"\bearnings per share\b",
                r"\btax invoice\b", r"\bgst number\b",
                r"\bpurchase order\b",
            ],
            "threshold": 3,
        },
    }

    # ── 2. POSITIVE CLASS DEFINITIONS ──────────────────────────────────────────
    CLASSES = {
        "HEALTH_POLICY": {
            "keywords": [
                r"policy schedule",
                r"sum insured",
                r"waiting period",
                r"standard exclusion",
                r"irdai",
                r"certificate of insurance",
                r"policy number",
                r"contract of insurance",
                r"in-patient hospitali[sz]ation",
                r"day care treatment",
                r"pre-existing disease",
                r"co-?payment",
                r"network hospital",
                r"grace period",
                r"renewal",
                r"insured person",
                r"restoration benefit",
                r"room rent",
                r"cumulative bonus",
            ],
            "weight": 3.0,
            "min_matches": 4,   # must match at least this many to be a strong candidate
        },
        "INSURANCE_BROCHURE": {
            "keywords": [
                r"marketing",
                r"brochure",
                r"why (choose|buy)",
                r"product highlight",
                r"illustrative",
                r"brochure code",
                r"usp\b",
                r"key benefits",
                r"tax benefit",
                r"for more (details|information)",
            ],
            "weight": 1.5,
            "min_matches": 2,
        },
        "CLAIM_REJECTION": {
            "keywords": [
                r"repudiation",
                r"rejection letter",
                r"claim not admitted",
                r"not payable",
                r"claim reference",
                r"repudiated",
                r"intimation of rejection",
                r"claim is hereby rejected",
            ],
            "weight": 2.5,
            "min_matches": 2,
        },
        "MEDICAL_RECORD": {
            "keywords": [
                r"chief complaints?",
                r"medical history",
                r"diagnosis",
                r"on examination",
                r"procedure",
                r"discharge summary",
                r"attending physician",
                r"final diagnosis",
                r"vitals",
                r"prescription",
                r"ward",
            ],
            "weight": 2.0,
            "min_matches": 3,
        },
        "HOSPITAL_BILL": {
            "keywords": [
                r"total amount (due|payable)",
                r"invoice number",
                r"final bill",
                r"amount payable",
                r"item-?wise breakup",
                r"summary of charges",
                r"room charges",
                r"consultation charges",
                r"hospital (name|registration)",
            ],
            "weight": 2.0,
            "min_matches": 2,
        },
    }

    # ── 3. STRUCTURAL PATTERNS (bonus points) ──────────────────────────────────
    STRUCTURAL_PATTERNS = [
        (r"\b(IRDAI|IRDA)\s*(Reg\.?\s*No\.?|Registration\s*No\.?)\s*[\d/]+", "irdai_reg_number"),
        (r"\bPolicy\s*(No\.?|Number)\s*[:\-]?\s*[A-Z0-9/\-]{5,}", "policy_number"),
        (r"\bSum\s+Insured\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*[\d,]+", "sum_insured_amount"),
        (r"\b(Premium)\s*[:\-]?\s*(?:Rs\.?|INR|₹)\s*[\d,]+", "premium_amount"),
        (r"\bRenewal\s+Due\s+Date\s*[:\-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "renewal_date"),
    ]

    # ── 4. STRONG DOMAIN KEYWORDS (required for final acceptance) ──────────────
    STRONG_DOMAIN_KEYWORDS = [
        r"hospitali[sz]ation",
        r"in-patient",
        r"domiciliary",
        r"irdai",
        r"pre-existing",
        r"co-?payment",
        r"ayush",
        r"network hospital",
        r"ambulance cover",
        r"maternity benefit",
    ]

    # ───────────────────────────────────────────────────────────────────────────

    def classify(self, text: str) -> ClassificationResult:
        if not text or not text.strip():
            return ClassificationResult(
                document_type="UNKNOWN", confidence=0.0,
                reasoning="Empty / blank document.",
                validation_score=0.0
            )

        text_lower = text.lower()

        # ── Layer 1: Negative Signal Guard ────────────────────────────────────
        triggered, neg_hits = self._check_negative_signals(text_lower)
        if triggered:
            label, reason = triggered
            return ClassificationResult(
                document_type="NON_INSURANCE",
                confidence=0.95,
                reasoning=f"Document identified as {label}. {reason}",
                validation_score=0.0,
                negative_signals=neg_hits,
            )

        # ── Layer 2: Multi-Class Keyword Scoring ──────────────────────────────
        scores, match_counts = self._score_classes(text_lower)
        best_cls = max(scores, key=scores.get)
        best_score = scores[best_cls]

        # No class scored above floor → generic non-insurance doc
        if best_score < 0.15:
            return ClassificationResult(
                document_type="NON_INSURANCE",
                confidence=0.88,
                reasoning="No insurance domain patterns found. Likely a generic or off-topic document.",
                validation_score=0.0,
            )

        # ── Layer 3: Structural Pattern Bonus ────────────────────────────────
        structural_hits = self._check_structural_patterns(text)
        structural_bonus = min(len(structural_hits) * 0.08, 0.3)

        # ── Layer 4: Composite Confidence ─────────────────────────────────────
        base_confidence = min(best_score / 2.0, 1.0)
        confidence = min(base_confidence + structural_bonus, 1.0)

        # Strong domain keywords check (for HEALTH_POLICY only)
        strong_hits = sum(1 for kw in self.STRONG_DOMAIN_KEYWORDS if re.search(kw, text_lower))

        reasoning = (
            f"Detected as {best_cls} "
            f"(keyword matches: {match_counts[best_cls]}, "
            f"structural signals: {len(structural_hits)}, "
            f"domain-specific terms: {strong_hits})."
        )

        return ClassificationResult(
            document_type=best_cls,
            confidence=round(confidence, 3),
            reasoning=reasoning,
            validation_score=round(confidence, 3),
            metadata={
                "structural_hits": structural_hits,
                "strong_domain_hits": strong_hits,
                "class_scores": {k: round(v, 3) for k, v in scores.items()},
                "match_counts": match_counts,
            },
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _check_negative_signals(self, text_lower: str):
        """Returns (label, reason) if a negative category is triggered, else None."""
        for label, cfg in self.NEGATIVE_SIGNALS.items():
            hits = [kw for kw in cfg["keywords"] if re.search(kw, text_lower)]
            if len(hits) >= cfg["threshold"]:
                reason = f"Found {len(hits)} characteristic term(s): {', '.join(hits[:5])}."
                return (label, reason), hits[:10]
        return None, []

    def _score_classes(self, text_lower: str):
        scores = {}
        match_counts = {}
        for cls, cfg in self.CLASSES.items():
            hits = sum(1 for kw in cfg["keywords"] if re.search(kw, text_lower))
            match_counts[cls] = hits
            # Normalise by total keywords, weight, then give partial credit if above min
            score = (hits / len(cfg["keywords"])) * cfg["weight"]
            # Penalise if below min_matches — the class score won't dominate
            if hits < cfg.get("min_matches", 1):
                score *= 0.4
            scores[cls] = score
        return scores, match_counts

    def _check_structural_patterns(self, text: str):
        """Returns list of pattern labels found in the original (case-sensitive) text."""
        found = []
        for pattern, label in self.STRUCTURAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(label)
        return found
