# tests/test_prepurchase_scoring.py

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from schemas.pre_purchase import ClauseRiskAssessment
from services.prepurchase_scoring import compute_policy_score


def test_perfect_policy_scoring():
    """
    Test a perfect policy with all Low Risk values and full compliance.
    Expected: Clamped to 100.
    """
    clause_risk = ClauseRiskAssessment(
        waiting_period="Low Risk",
        pre_existing_disease="Low Risk",
        room_rent_sublimit="Low Risk",
        disease_specific_caps="Low Risk",
        co_payment="Low Risk",
        exclusions_clarity="Low Risk",
        claim_procedure_complexity="Low Risk",
        sublimits_and_caps="Low Risk",
        restoration_benefit="Low Risk",
        transparency_of_terms="Low Risk"
    )
    compliance_data = {"compliance_score": 7.0}  # 100% compliance
    
    result = compute_policy_score(clause_risk, compliance_data)
    score = result["adjusted_score"]
    
    print(f"Perfect Policy Score: {score} (Expected 100.0)")
    assert score == 100.0, f"Expected perfect score of 100.0, got {score}"
    assert len(result["red_flags"]) == 0, "Should have 0 red flags for a perfect policy"
    assert len(result["positive_flags"]) > 0, "Should list positive highlights"


def test_standard_moderate_policy_scoring():
    """
    Test a policy with standard moderate limits:
    - Moderate waiting period, Moderate co-payment, Moderate room rent
    - Standard compliance score of 5/7
    """
    clause_risk = ClauseRiskAssessment(
        waiting_period="Moderate Risk",  # -4
        pre_existing_disease="Low Risk",  # +4
        room_rent_sublimit="Moderate Risk",  # -7
        disease_specific_caps="Low Risk",  # +4
        co_payment="Moderate Risk",  # -8
        exclusions_clarity="Low Risk",  # +2
        claim_procedure_complexity="Low Risk",  # +2
        sublimits_and_caps="Low Risk",  # +3
        restoration_benefit="Low Risk",  # +6
        transparency_of_terms="Low Risk"  # +2
    )
    compliance_data = {"compliance_score": 5.0}  # 5/7 compliance
    
    result = compute_policy_score(clause_risk, compliance_data)
    score = result["adjusted_score"]
    
    # Math calculation:
    # Base: 80.0
    # Deductions: Room rent (-7) + Co-pay (-8) + Waiting period (-4) = -19.0
    # Boosts: PED (+4) + Specific caps (+4) + Exclusions (+2) + Claim (+2) + Sublimits (+3) + Restoration (+6) + Transparency (+2) = +23.0
    # Compliance: (5.0 / 7.0) * 10 = +7.14
    # Expected unrounded count: 80.0 - 19.0 + 23.0 + 7.14 = 91.14
    print(f"Moderate Policy Score Details: {result}")
    print(f"Moderate Policy Score: {score} (Expected ~91.14)")
    assert 90.0 < score < 92.0, f"Expected score around 91.14, got {score}"


def test_high_financial_risk_scoring():
    """
    Test a policy carrying high direct financial exposure:
    - High Risk co-payment (-15)
    - High Risk room rent sublimits (-15)
    - No restoration benefit mentioned (-8)
    - High Risk pre-existing disease duration (-12)
    - 0 compliance score
    """
    clause_risk = ClauseRiskAssessment(
        co_payment="High Risk",
        room_rent_sublimit="High Risk",
        restoration_benefit="Not Mentioned",
        pre_existing_disease="High Risk",
        disease_specific_caps="Low Risk",
        waiting_period="Low Risk",
        sublimits_and_caps="Low Risk",
        exclusions_clarity="Low Risk",
        claim_procedure_complexity="Low Risk",
        transparency_of_terms="Low Risk"
    )
    compliance_data = {"compliance_score": 0.0}
    
    result = compute_policy_score(clause_risk, compliance_data)
    score = result["adjusted_score"]
    
    # Math calculation:
    # Base: 80.0
    # Deductions: Co-pay (-15) + Room Rent (-15) + Restoration (-8) + PED (-12) = -50.0
    # Boosts: Disease caps (+4) + Waiting period (+3) + Sublimits (+3) + Exclusions (+2) + Claim (+2) + Transparency (+2) = +16.0
    # Net: 80.0 - 50.0 + 16.0 = 46.0
    print(f"High Financial Risk Score: {score} (Expected 46.0)")
    assert score == 46.0, f"Expected score of 46.0, got {score}"
    assert len(result["red_flags"]) == 4, "Should flag Co-Pay, Room Rent, Restoration, and PED as red flags"


def test_systemic_risk_penalty():
    """
    Test the systemic risk penalty multiplier trigger:
    When 60% or more clauses are High Risk
    """
    clause_risk = ClauseRiskAssessment(
        waiting_period="High Risk",
        pre_existing_disease="High Risk",
        room_rent_sublimit="High Risk",
        disease_specific_caps="High Risk",
        co_payment="High Risk",
        sublimits_and_caps="High Risk",  # 6 / 10 clauses are High Risk
        exclusions_clarity="Low Risk",
        claim_procedure_complexity="Low Risk",
        restoration_benefit="Low Risk",
        transparency_of_terms="Low Risk"
    )
    compliance_data = {"compliance_score": 0.0}
    
    result = compute_policy_score(clause_risk, compliance_data)
    score = result["adjusted_score"]
    
    # Math:
    # Base: 80.0
    # Deductions: 6 High Risk clauses ->
    #   Waiting period (-10)
    #   PED (-12)
    #   Room rent (-15)
    #   Disease caps (-12)
    #   Co-pay (-15)
    #   Sublimits (-10)
    #   Total: -74.0
    # Systemic risk penalty: -15.0
    # Boosts: Exclusions (+2) + Claim (+2) + Restoration (+6) + Transparency (+2) = +12.0
    # Net calculated score: 80.0 - 74.0 - 15.0 + 12.0 = 3.0
    print(f"Systemic Risk Score: {score} (Expected 3.0)")
    assert score == 3.0, f"Expected systemic risk clamped score of 3.0, got {score}"
    assert any("Systemic risk" in flag for flag in result["red_flags"]), "Systemic risk flag must be appended"


def test_not_found_vs_not_mentioned():
    """
    Verify different weights for OCR omissions ('Not Found') vs policy omissions ('Not Mentioned').
    e.g., Room Rent & Restoration.
    """
    # 1. Not Found (Assumed OCR omission, 0 penalty)
    clause_risk_nf = ClauseRiskAssessment(
        room_rent_sublimit="Not Found",
        restoration_benefit="Not Found"
    )
    res_nf = compute_policy_score(clause_risk_nf, None)
    
    # 2. Not Mentioned (Assumed policy omission, penalty applies)
    clause_risk_nm = ClauseRiskAssessment(
        room_rent_sublimit="Not Mentioned",
        restoration_benefit="Not Mentioned"
    )
    res_nm = compute_policy_score(clause_risk_nm, None)
    
    score_nf = res_nf["adjusted_score"]
    score_nm = res_nm["adjusted_score"]
    
    print(f"Not Found Score: {score_nf} vs Not Mentioned Score: {score_nm}")
    assert score_nm < score_nf, "Not Mentioned (policy omission) must carry a deduction penalty compared to Not Found (OCR limits)"


if __name__ == "__main__":
    print("🧪 Running Pre-Purchase Scoring Engine Validation tests...")
    test_perfect_policy_scoring()
    test_standard_moderate_policy_scoring()
    test_high_financial_risk_scoring()
    test_systemic_risk_penalty()
    test_not_found_vs_not_mentioned()
    print("✨ ALL PRE-PURCHASE SCORING TESTS PASSED")
