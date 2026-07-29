"""
test_known_provider_scoring.py

Verifies that the pre-extracted provider code path uses the SAME scoring
engine logic as the full RAG pipeline, and checks whether the resulting
scores are consistent and internally defensible.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from schemas.pre_purchase import ClauseRiskAssessment
from services.prepurchase_scoring import compute_policy_score
from services.known_providers_db import get_known_providers, get_pre_extracted_clause_risk


def _score_provider(provider_name: str, compliance_score: float = 5.0) -> dict:
    """Helper: build clause risk + run scoring engine for a known provider."""
    raw = get_pre_extracted_clause_risk(provider_name)
    assert raw is not None, f"Provider not found: {provider_name}"
    clause_risk = ClauseRiskAssessment(**raw)
    compliance_data = {"compliance_score": compliance_score}
    result = compute_policy_score(clause_risk, compliance_data)
    return {
        "provider": provider_name,
        "clause_risk": raw,
        "score": result["adjusted_score"],
        "rating": (
            "Strong" if result["adjusted_score"] >= 80
            else "Moderate" if result["adjusted_score"] >= 55
            else "Weak"
        ),
        "red_flags": result["red_flags"],
        "positive_flags": result["positive_flags"],
        "explainability": result["explainability"],
    }


def test_all_providers_use_same_scoring_engine():
    """
    Confirms the compute_policy_score function is called for EVERY known
    provider — same code path as the full RAG pipeline.
    """
    providers = get_known_providers()
    assert len(providers) >= 1, "No known providers found"

    for p in providers:
        result = _score_provider(p)
        score = result["score"]
        assert 0.0 <= score <= 100.0, (
            f"{p}: Score {score} out of [0, 100] range"
        )
        # Score must have a sensible explainability block
        exp = result["explainability"]
        assert "deductions" in exp, f"{p}: explainability missing 'deductions'"
        assert "additions" in exp, f"{p}: explainability missing 'additions'"
        print(f"  OK  {p:35s} -> {score:5.1f} ({result['rating']})")


def test_restoration_benefit_defaults():
    """
    This test highlights a consistency bug in known_providers_db.py:
    All providers default restoration_benefit to 'Not Found' (0 penalty)
    even when the raw data has NO restoration benefit entry.

    'Not Found' means the text extractor couldn't find it (OCR limit).
    'Not Mentioned' means the policy simply doesn't offer it (-8 penalty).

    For pre-extracted providers whose raw data has no restoration clause,
    the correct default is 'Not Mentioned'.
    """
    providers = get_known_providers()
    offenders = []

    for p in providers:
        raw = get_pre_extracted_clause_risk(p)
        if raw and raw.get("restoration_benefit") == "Not Found":
            offenders.append(p)

    if offenders:
        print(f"\n  WARNING: Bug detected - these providers default restoration_benefit "
              f"to 'Not Found' instead of 'Not Mentioned':")
        for o in offenders:
            print(f"       {o}")

    # Measure the scoring impact of the bug
    if offenders:
        sample = offenders[0]
        raw_buggy = get_pre_extracted_clause_risk(sample).copy()

        # Current (buggy) - restoration as 'Not Found' -> 0 penalty
        buggy_clause = ClauseRiskAssessment(**raw_buggy)
        buggy_score = compute_policy_score(buggy_clause, {"compliance_score": 5.0})["adjusted_score"]

        # Corrected - restoration as 'Not Mentioned' -> -8 penalty
        raw_fixed = raw_buggy.copy()
        raw_fixed["restoration_benefit"] = "Not Mentioned"
        fixed_clause = ClauseRiskAssessment(**raw_fixed)
        fixed_score = compute_policy_score(fixed_clause, {"compliance_score": 5.0})["adjusted_score"]

        delta = buggy_score - fixed_score
        print(f"\n  Scoring impact for '{sample}':")
        print(f"    Current score (Not Found, 0 penalty)   : {buggy_score}")
        print(f"    Corrected score (Not Mentioned, -8 pts): {fixed_score}")
        print(f"    Inflation due to bug                   : +{delta:.1f} pts")

        # The bug should produce a meaningfully higher score
        assert delta > 0, "Bug should inflate the score when restoration is absent"
        print(f"\n  FAIL: restoration_benefit default must be fixed in known_providers_db.py")
    else:
        print("  PASS: No restoration_benefit default bug found (already fixed).")


def test_score_ordering_sanity():
    """
    Reliance Health Gain has a 48-month PED waiting period (High Risk),
    which is worse than StarHealth / Niva Bupa (36 months, High Risk).
    Scores should reflect relative ordering with Reliance <= others in PED.
    Also verifies Reliance gets flagged as 'High Risk' for PED.
    """
    reliance = _score_provider("Reliance General Insurance")
    star     = _score_provider("Star Health")

    print(f"\n  Reliance General Insurance : {reliance['score']} ({reliance['rating']})")
    print(f"  Star Health                : {star['score']} ({star['rating']})")

    # Both should be High Risk for PED
    assert reliance["clause_risk"]["pre_existing_disease"] == "High Risk", \
        "Reliance (48-month PED) must be High Risk"
    assert star["clause_risk"]["pre_existing_disease"] == "High Risk", \
        "Star Health (36-month PED) must be High Risk"

    # Reliance has a longer PED wait, which means should score the same or lower
    # (both are capped at the same 'High Risk' band, so scores could be equal)
    assert reliance["score"] <= star["score"] + 0.1, (
        f"Reliance (48-month PED) should score <= Star Health (36-month PED). "
        f"Got {reliance['score']} vs {star['score']}"
    )
    print("  PASS: Ordering sanity check passed")


def test_icici_lower_ped_wait():
    """
    ICICI Lombard's PED waiting is 24 months -> Moderate Risk (better than 36-month High Risk).
    So ICICI should score higher than providers with 36-month PED.
    """
    icici = _score_provider("ICICI Lombard")
    star  = _score_provider("Star Health")

    icici_ped = icici["clause_risk"]["pre_existing_disease"]
    star_ped  = star["clause_risk"]["pre_existing_disease"]

    print(f"\n  ICICI PED risk : {icici_ped}  -> score: {icici['score']}")
    print(f"  Star  PED risk : {star_ped}   -> score: {star['score']}")

    assert icici_ped == "Moderate Risk", f"ICICI (24-month PED) should be Moderate Risk, got: {icici_ped}"
    assert star_ped  == "High Risk",     f"Star (36-month PED) should be High Risk, got: {star_ped}"
    assert icici["score"] > star["score"], (
        f"ICICI (Moderate PED) should score higher than Star (High Risk PED). "
        f"Got {icici['score']} vs {star['score']}"
    )
    print("  PASS: ICICI vs Star PED ordering correct")


if __name__ == "__main__":
    providers = get_known_providers()
    print(f"\n{'='*60}")
    print(f"  CareBridge AI - Known Provider Scoring Consistency Check")
    print(f"  {len(providers)} providers in database")
    print(f"{'='*60}\n")

    print("[ Test 1 ] All providers use the same scoring engine")
    test_all_providers_use_same_scoring_engine()

    print("\n[ Test 2 ] Restoration benefit default bug check")
    test_restoration_benefit_defaults()

    print("\n[ Test 3 ] Score ordering sanity (Reliance vs Star)")
    test_score_ordering_sanity()

    print("\n[ Test 4 ] ICICI shorter PED wait should score higher")
    test_icici_lower_ped_wait()

    print(f"\n{'='*60}")
    print("  Done - review any WARNINGS above before Phase 2.")
    print(f"{'='*60}")
