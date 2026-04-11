from engines.pre_purchase_engine import PrePurchaseEngine
from schemas.pre_purchase import PrePurchaseReport
import json

class MockModel: pass
class MockTokenizer: pass

def test_engine():
    engine = PrePurchaseEngine(MockModel(), MockTokenizer())
    
    # Mock the 'generate' function
    import engines.pre_purchase_engine
    
    def mock_generate(*args, **kwargs):
        return json.dumps({
            "clause_risk": {
                "waiting_period": "High Risk",
                "pre_existing_disease": "Moderate Risk"
            },
            "agent_validation": {
                "is_consistent": False,
                "claims": [
                    {"claim": "Claim 1", "fact_check": "Fact 1", "is_correct": False, "source_citation": "Old Cite"},
                    {"claim": "Claim 2", "fact_check": "Fact 2", "is_correct": False, "citation": "New Cite"},
                    {"claim": "Claim 3", "fact_check": "Fact 3", "is_correct": False},
                    {"claim": "Claim 4", "fact_check": "Fact 4", "is_correct": False},
                    {"claim": "Claim 5", "fact_check": "Fact 5", "is_correct": False},
                ],
                "trust_score": 45.0
            },
            "regulatory_citations": [
                "Section 1", "Section 1", "Section 2", "Section 3", "Section 4", "Section 5", "Section 6"
            ],
            "checklist_for_buyer": [
                "Step 1", "Step 2", "Step 3", "Step 4", "Step 5"
            ],
            "red_flags": ["R1", "R2", "R3", "R4"]
        })

    # Manually monkeypatch generate
    original_generate = engines.pre_purchase_engine.generate
    engines.pre_purchase_engine.generate = mock_generate
    
    engine.irdai_retriever = None
    engine.standard_retriever = None

    try:
        report = engine.run("Fake policy text", agent_summary="Fake agent summary")
        
        print(f"--- Verification Results ---")
        
        # Check Compression
        print(f"Discrepancies count: {len(report.agent_validation.discrepancies)} (Expected <= 4)")
        assert len(report.agent_validation.discrepancies) == 4
        
        print(f"Regulatory citations count: {len(report.regulatory_citations)} (Expected <= 5)")
        assert len(report.regulatory_citations) == 5
        
        print(f"Checklist count: {len(report.checklist_for_buyer)} (Expected <= 4)")
        assert len(report.checklist_for_buyer) == 4
        
        print(f"Red flags count: {len(report.red_flags)} (Expected <= 3)")
        assert len(report.red_flags) == 3

        # Check Legacy Fallback
        print(f"Claim 1 citation: {report.agent_validation.discrepancies[0].citation} (Expected 'Old Cite')")
        assert report.agent_validation.discrepancies[0].citation == "Old Cite"
        
        print(f"Claim 2 citation: {report.agent_validation.discrepancies[1].citation} (Expected 'New Cite')")
        assert report.agent_validation.discrepancies[1].citation == "New Cite"
        
        print("\n✅ Verification SUCCESS: Engine normalization and compression logic is correct.")
        
    finally:
        engines.pre_purchase_engine.generate = original_generate

if __name__ == "__main__":
    test_engine()
