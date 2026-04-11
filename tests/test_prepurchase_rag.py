import pytest
from engines.pre_purchase_engine import PrePurchaseEngine
from schemas.pre_purchase import PrePurchaseReport
import json

class MockModel:
    pass

class MockTokenizer:
    pass

@pytest.fixture
def engine():
    return PrePurchaseEngine(MockModel(), MockTokenizer())

def test_engine_normalization_and_compression(engine, monkeypatch):
    # Mock the 'generate' function to return a messy, oversized JSON
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
                    {"claim": "Claim 5", "fact_check": "Fact 5", "is_correct": False}, # Should be capped
                ],
                "trust_score": 45.0
            },
            "regulatory_citations": [
                "Section 1", "Section 1", "Section 2", "Section 3", "Section 4", "Section 5", "Section 6"
            ],
            "checklist_for_buyer": [
                "Step 1", "Step 2", "Step 3", "Step 4", "Step 5"
            ]
        })

    monkeypatch.setattr("engines.pre_purchase_engine.generate", mock_generate)
    
    # Mock RAG retrievers to None to avoid init errors in test if indices missing
    engine.irdai_retriever = None
    engine.standard_retriever = None

    report = engine.run("Fake policy text", agent_summary="Fake agent summary")
    
    assert isinstance(report, PrePurchaseReport)
    
    # Check Compression (Capping)
    assert len(report.agent_validation.discrepancies) <= 4
    assert len(report.regulatory_citations) <= 5
    assert len(report.checklist_for_buyer) <= 4
    
    # Check Deduplication
    assert len(report.regulatory_citations) == len(set(report.regulatory_citations))
    
    # Check Legacy Fallback (source_citation -> citation)
    first_claim = report.agent_validation.discrepancies[0]
    assert first_claim.citation == "Old Cite"
    
    second_claim = report.agent_validation.discrepancies[1]
    assert second_claim.citation == "New Cite"

    print("✅ Pre-Purchase RAG Engine Integration Test Passed!")

if __name__ == "__main__":
    pytest.main([__file__])
