
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from rules.irdai_rules import run_all_irdai_checks, format_irdai_findings
from rules.broker_risk_engine import BrokerRiskEngine

def test_hard_logic():
    print("🔄 Testing Deterministic IRDAI Rules...")
    rejection = "Your claim is rejected. We don't cover this."
    policy = "Policy start: 2024."
    
    # This should trigger "Missing Clause Citation" rule
    findings = run_all_irdai_checks(rejection, policy)
    formatted = format_irdai_findings(findings)
    print(formatted)
    
    assert any("Specific Policy Clause" in f['rule'] for f in findings), "Should detect missing clause citation"
    print("✅ IRDAI Rules Logic Verified.")

    print("\n🔄 Testing Broker Risk Engine...")
    risk_engine = BrokerRiskEngine()
    # Rejection citing non-disclosure of diabetes
    rejection_text = "Rejected due to non-disclosure of pre-existing diabetes."
    risk_data = risk_engine.analyze_misrepresentation(rejection_text, {})
    
    print(f"Risk Score: {risk_data['risk_score']}")
    print(f"Risk Level: {risk_data['risk_level']}")
    
    assert risk_data['risk_score'] >= 0.5, "Should have high risk score for non-disclosure"
    print("✅ Broker Risk Engine Verified.")

    print("\n✨ ALL DETERMINISTIC LOGIC TESTS PASSED")

if __name__ == "__main__":
    test_hard_logic()
