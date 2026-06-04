
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from engines.post_rejection_engine import PostRejectionEngine
from schemas.request import PostRejectionRequest
from llm.model_loader import ModelLoader

def test_integration():
    print("🔄 Initializing Model...")
    loader = ModelLoader()
    model, tokenizer = loader.get_model()
    
    engine = PostRejectionEngine(model, tokenizer)
    
    # Mock request
    request = PostRejectionRequest(
        policy_text="""
        HEALTH INSURANCE POLICY.
        Pre-existing Disease Waiting Period: 48 months.
        Co-payment: 20%.
        """,
        rejection_text="""
        Your claim for diabetes is rejected because it is a pre-existing 
        disease not disclosed at inception. Rejection as per Clause 4.2.
        """,
        medical_text="Patient has history of hyperglycemia since 2020.",
        user_explanation="I was unaware of the condition during purchase."
    )
    
    print("🔄 Running Audit Engine...")
    report = engine.run(request)
    
    print("\n✅ AUDIT REPORT GENERATED")
    print("-" * 50)
    print(f"Verdict/Score: {report.appeal_strength.label} ({report.appeal_strength.percentage}%)")
    print(f"Policy Clause: {report.policy_clause_detected}")
    
    if report.risk_data:
        print(f"Risk Score:    {report.risk_data.risk_score}")
        print(f"Risk Level:    {report.risk_data.risk_level}")
        print(f"Risk Action:   {report.risk_data.action}")
    else:
        print("❌ Risk Data Missing!")

    print("-" * 50)
    
    # Assertions
    assert report.risk_data is not None, "Risk data must be generated"
    assert report.risk_data.risk_score > 0, "Risk score should be positive for non-disclosure"
    print("✨ ALL BACKEND INTEGRATION TESTS PASSED")

if __name__ == "__main__":
    test_integration()
