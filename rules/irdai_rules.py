"""
CareBridge AI — IRDAI Regulatory Rules
========================================
Deterministic validators grounded in actual IRDAI regulations.

Each function returns a dict:
{
    "applicable": bool,
    "rule": str,       # short rule name
    "finding": str,    # what was found
    "protection": str, # the legal protection / IRDAI citation
    "severity": str,   # "Critical" | "High" | "Medium" | "Info"
}

Used by the rejection engine BEFORE LLM stage to catch
black-and-white rule violations that don't need AI interpretation.
"""

from __future__ import annotations

import re
from typing import Optional


# ─────────────────────────────────────────────
# Rule 1: Moratorium Rule (8-Year)
# IRDAI Health Insurance Regulations 2016 §13
# ─────────────────────────────────────────────

def check_moratorium_rule(
    rejection_text: str,
    policy_text: str,
    years_of_coverage: Optional[int] = None,
) -> dict:
    """
    IRDAI §13: After 8 continuous years of coverage, no claim can be denied
    on grounds of pre-existing disease or non-disclosure.
    This rule is ABSOLUTE — no exceptions.
    """
    combined = (rejection_text + " " + policy_text).lower()

    # Detect PED / non-disclosure rejection
    is_ped_rejection = any(re.search(p, combined, re.IGNORECASE) for p in [
        r"\bpre.?existing\b", r"\bnon.disclosure\b", r"\bnot\s+disclosed\b",
        r"\bprior\s+condition\b", r"\bpre.?existing\s+disease\b",
    ])

    # Detect 8+ year tenure signals in policy text
    tenure_patterns = [
        r"\b(eight|8)\s*.?year[s]?\b",
        r"\b(9|10|11|12|13|14|15|20)\s*.?year[s]?\s*(of\s+)?(continuous|uninterrupted)\b",
        r"\bpolicy\s+since\s+(200[0-8]|199\d)\b",   # long-running policy
        r"\bcontinuously\s+renew(ed|ing)\s+for\s+\d+\b",
    ]
    has_long_tenure = (
        any(re.search(p, combined, re.IGNORECASE) for p in tenure_patterns)
        or (years_of_coverage is not None and years_of_coverage >= 8)
    )

    applicable = is_ped_rejection and has_long_tenure

    return {
        "applicable": applicable,
        "rule": "Moratorium Rule (8-Year)",
        "finding": (
            "Policy appears to have 8+ years of continuous coverage. "
            "PED/non-disclosure rejection may be in violation of IRDAI §13."
        ) if applicable else (
            "8-year moratorium rule: not triggered for this case."
        ),
        "protection": (
            "IRDAI Health Insurance Regulations 2016 §13: After 8 continuous years of coverage, "
            "NO insurer can reject a claim on grounds of non-disclosure or pre-existing disease. "
            "This rule is absolute and overrides all policy terms."
        ),
        "severity": "Critical" if applicable else "Info",
    }


# ─────────────────────────────────────────────
# Rule 2: Claim Settlement Timeline
# IRDAI Master Circular 2024
# ─────────────────────────────────────────────

def check_settlement_timeline(rejection_text: str, days_since_filing: Optional[int] = None) -> dict:
    """
    IRDAI Master Circular 2024: Reimbursement claims must be settled within 30 days.
    If delayed, insurer must pay interest at 2% above bank rate.
    """
    breach_patterns = [
        r"\bpending\s+(since|for)\s+\d+\s+(days?|months?)\b",
        r"\bno\s+response\s+(in|for|within)\s+\d+\s+days?\b",
        r"\bdelayed?\s+(settlement|payment|response)\b",
    ]

    has_delay_signal = any(
        re.search(p, rejection_text, re.IGNORECASE) for p in breach_patterns
    )
    days_breach = days_since_filing is not None and days_since_filing > 30

    applicable = has_delay_signal or days_breach

    return {
        "applicable": applicable,
        "rule": "Claim Settlement Timeline (30 Days)",
        "finding": (
            f"Settlement delay detected — {days_since_filing} days since filing."
            if days_breach else
            "Potential settlement delay mentioned in documents."
        ) if applicable else "No settlement delay detected.",
        "protection": (
            "IRDAI Master Circular 2024: Reimbursement claims must be settled within 30 days "
            "of receiving all documents. Delay triggers interest at 2% above RBI bank rate per month."
        ),
        "severity": "High" if applicable else "Info",
    }


# ─────────────────────────────────────────────
# Rule 3: Rejection Must Cite Specific Clause
# IRDAI Protection of Policyholders 2017
# ─────────────────────────────────────────────

def check_clause_citation(rejection_text: str) -> dict:
    """
    IRDAI Protection of Policyholders 2017 §9:
    A rejection letter MUST cite the specific policy clause being invoked.
    Vague rejections ("not covered") without clause reference are challengeable.
    """
    # Positive signals — clause was cited
    citation_patterns = [
        r"\bclause\s+\d+[\.\d]*\b",
        r"\bsection\s+\d+[\.\d]*\b",
        r"\bschedule\s+[IVXLC\d]+\b",
        r"\bunder\s+clause\b",
        r"\bas\s+per\s+(clause|section)\b",
        r"\bprovision\s+\d+\b",
    ]
    has_clause_citation = any(
        re.search(p, rejection_text, re.IGNORECASE) for p in citation_patterns
    )

    # Vague rejection signals — no specific clause
    vague_patterns = [
        r"\bnot\s+covered\s*[.\!]\s*$",
        r"\boutside\s+coverage\s*[.\!]\s*$",
        r"\bnot\s+admissible\s*[.\!]\s*$",
    ]
    is_vague = any(
        re.search(p, rejection_text[:500], re.IGNORECASE) for p in vague_patterns
    )

    applicable = not has_clause_citation or is_vague

    return {
        "applicable": applicable,
        "rule": "Rejection Must Cite Specific Policy Clause",
        "finding": (
            "Rejection letter does not appear to cite a specific policy clause. "
            "This is a procedural violation."
        ) if applicable else (
            "Rejection letter contains a policy clause citation."
        ),
        "protection": (
            "IRDAI Protection of Policyholders Regulations 2017 §9: "
            "Every rejection must be communicated in writing with the specific policy clause invoked. "
            "Vague rejections that don't cite a clause can be challenged at the Ombudsman."
        ),
        "severity": "High" if applicable else "Info",
    }


# ─────────────────────────────────────────────
# Rule 4: Waiting Period Disclosure
# IRDAI Health Insurance Regulations 2016
# ─────────────────────────────────────────────

def check_waiting_period_disclosure(rejection_text: str, policy_text: str) -> dict:
    """
    IRDAI: Waiting periods must be disclosed in the policy schedule at inception.
    An undisclosed waiting period applied after a claim is a violation.
    """
    # Rejection invokes waiting period
    wp_rejection = any(re.search(p, rejection_text, re.IGNORECASE) for p in [
        r"\bwaiting\s+period\b", r"\binitial\s+waiting\b"
    ])

    # But waiting period not mentioned in policy text
    wp_in_policy = any(re.search(p, policy_text, re.IGNORECASE) for p in [
        r"\bwaiting\s+period\b", r"\bwaiting\s+period\s+of\s+\d+\b"
    ])

    applicable = wp_rejection and policy_text and not wp_in_policy

    return {
        "applicable": applicable,
        "rule": "Waiting Period Must Be Disclosed at Policy Issuance",
        "finding": (
            "Waiting period cited in rejection but not found in provided policy text — "
            "possible undisclosed condition."
        ) if applicable else (
            "Waiting period clause appears to be present in policy."
        ),
        "protection": (
            "IRDAI Health Insurance Regulations 2016 §8: "
            "All waiting periods must be explicitly disclosed in the policy schedule "
            "and communicated at inception. Applying an undisclosed waiting period is unlawful."
        ),
        "severity": "High" if applicable else "Info",
    }


# ─────────────────────────────────────────────
# Rule 5: Standardized Exclusion Check
# IRDAI Standardization of Exclusions 2019
# ─────────────────────────────────────────────

# Only these exclusions are permitted by IRDAI 2019
_ALLOWED_EXCLUSIONS = {
    "cosmetic", "aesthetic", "dental", "vision", "spectacles",
    "infertility", "reproductive", "obesity", "weight", "hazardous sports",
    "self-inflicted", "war", "nuclear", "substance abuse",
    "congenital external", "naturopathy",
}


def check_exclusion_validity(rejection_text: str) -> dict:
    """
    IRDAI Standardization of Exclusions 2019:
    Insurers can only apply exclusions in the IRDAI-approved list.
    Any exclusion outside this list is challengeable.
    """
    text_lower = rejection_text.lower()

    # Check if the rejection cites a non-standard exclusion
    is_standard = any(exc in text_lower for exc in _ALLOWED_EXCLUSIONS)

    # Explicit exclusion clause pattern
    has_exclusion = bool(re.search(r"\bexclud(ed|ion)\b", text_lower, re.IGNORECASE))

    # If there's an exclusion cited but it's not in the standard list
    potentially_non_standard = has_exclusion and not is_standard

    return {
        "applicable": potentially_non_standard,
        "rule": "Exclusion Must Be in IRDAI Standardized List",
        "finding": (
            "Exclusion cited in rejection may not be on the IRDAI 2019 standardized list — "
            "verify if this exclusion is permitted."
        ) if potentially_non_standard else (
            "Exclusion appears to be a standard IRDAI-recognized category."
        ),
        "protection": (
            "IRDAI Guidelines on Standardization of Exclusions 2019: "
            "Only exclusions explicitly approved by IRDAI may be applied. "
            "Any exclusion outside the approved list is legally challengeable."
        ),
        "severity": "High" if potentially_non_standard else "Info",
    }


# ─────────────────────────────────────────────
# Rule 6: Late Intimation Cannot Be Sole Reason
# IRDAI Master Circular 2024
# ─────────────────────────────────────────────

def check_late_intimation_rule(rejection_text: str) -> dict:
    """
    IRDAI Master Circular 2024:
    Late intimation ALONE is not sufficient grounds for claim rejection.
    Insurer must prove prejudice caused by the delay.
    """
    is_late_intimation = any(re.search(p, rejection_text, re.IGNORECASE) for p in [
        r"\blate\s+intimation\b",
        r"\bnot\s+intimated\s+(within|in\s+time)\b",
        r"\bbeyond\s+the\s+(stipulated|specified)\s+(time|period)\b",
    ])

    # If ONLY late intimation and no other rejection reason
    other_reasons = any(re.search(p, rejection_text, re.IGNORECASE) for p in [
        r"\bpre.?existing\b", r"\bexclud\b", r"\bwaiting\s+period\b",
        r"\bnon.disclosure\b", r"\bfraud\b", r"\blapsed?\b",
    ])

    applicable = is_late_intimation and not other_reasons

    return {
        "applicable": applicable,
        "rule": "Late Intimation Alone Insufficient for Rejection",
        "finding": (
            "Rejection appears to be based solely on late intimation, which is not "
            "a valid standalone rejection reason under IRDAI 2024 guidelines."
        ) if applicable else (
            "Late intimation alone is not the cited rejection reason."
        ),
        "protection": (
            "IRDAI Master Circular 2024: Late intimation alone cannot be the only grounds "
            "for claim rejection. The insurer must demonstrate actual prejudice caused by the delay."
        ),
        "severity": "Critical" if applicable else "Info",
    }


# ─────────────────────────────────────────────
# Combined validator
# ─────────────────────────────────────────────

def run_all_irdai_checks(
    rejection_text: str,
    policy_text: str = "",
    days_since_filing: Optional[int] = None,
    years_of_coverage: Optional[int] = None,
) -> list[dict]:
    """
    Run all IRDAI rule validators and return list of applicable findings.
    Only returns rules where applicable=True or severity="Critical".
    """
    checks = [
        check_moratorium_rule(rejection_text, policy_text, years_of_coverage),
        check_settlement_timeline(rejection_text, days_since_filing),
        check_clause_citation(rejection_text),
        check_waiting_period_disclosure(rejection_text, policy_text),
        check_exclusion_validity(rejection_text),
        check_late_intimation_rule(rejection_text),
    ]

    # Return only actionable findings
    return [c for c in checks if c["applicable"] or c["severity"] == "Critical"]


def format_irdai_findings(findings: list[dict]) -> str:
    """Format IRDAI rule findings as a readable string for the report."""
    if not findings:
        return "No specific IRDAI rule violations detected."

    lines = ["IRDAI Regulatory Findings:"]
    for f in findings:
        sev = f.get("severity", "Info")
        marker = "⚠️" if sev == "Critical" else "⚡" if sev == "High" else "ℹ️"
        lines.append(f"\n{marker} [{sev}] {f['rule']}")
        lines.append(f"   Finding: {f['finding']}")
        lines.append(f"   Protection: {f['protection'][:120]}...")

    return "\n".join(lines)
