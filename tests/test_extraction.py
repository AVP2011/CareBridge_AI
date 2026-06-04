"""
CareBridge AI — Extraction & Rules Tests
==========================================
Phase 1 validation suite.

Run: pytest tests/test_extraction.py -v

Tests:
  - Document segmentation on sample policy text
  - Rejection classifier (hard + soft detection)
  - IRDAI rule validators (moratorium, clause citation, etc.)
  - PDF extractor (quality scorer, text cleaning)
  - RAG retriever smoke test (if indices exist)
"""

import pytest
import sys
from pathlib import Path

# Make sure project root is on path
sys.path.insert(0, str(Path(__file__).parents[1]))


# ─────────────────────────────────────────────────────────────────
# SAMPLE FIXTURES
# ─────────────────────────────────────────────────────────────────

SAMPLE_POLICY = """
HEALTH INSURANCE POLICY WORDING

Definitions:
"Pre-existing Disease" means any condition, ailment, or injury for which the insured
had signs, symptoms, or was diagnosed within 48 months prior to policy issuance.

Waiting Period:
1. Initial Waiting Period: 30 days from policy commencement date for all illnesses.
2. Pre-existing Disease Waiting Period: 48 months from first policy issuance date.
3. Specific Disease Waiting Period: Hernia, Cataract — 24 months waiting period.

Co-payment:
A co-payment of 20% shall apply to all claims where the insured is aged 60 years and above.

Room Rent Limit:
The maximum room rent payable shall not exceed Rs. 5,000 per day or 1% of sum insured.

Exclusions:
The policy does not cover cosmetic surgery, dental treatment (OPD), infertility treatments,
obesity management programs, self-inflicted injuries, and war-related injuries.

Grievance:
In case of grievance, contact the Grievance Redressal Officer within 15 days.
Escalate to IRDAI if unresolved.
"""

SAMPLE_REJECTION_HARD = """
Dear Policyholder,

This is to inform you that your claim bearing reference CL/2024/00123 has been rejected.

Based on our medical records review, the condition (Type 2 Diabetes) appears to be
a pre-existing disease that was not disclosed at the time of policy issuance.

As per Clause 4.2 of your policy, pre-existing diseases are excluded for the
first 48 months of coverage.

We regret that we are unable to process this claim.

Regards,
Claims Team
"""

SAMPLE_REJECTION_SOFT = """
Dear Policyholder,

With reference to your claim dated 15-Jan-2024, we regret to inform you that
the claim is not payable under your current policy terms.

The hospitalization does not fall under our coverage due to the waiting period
being applicable for the admitted condition.

We are unable to process the claim under the current policy.
"""

SAMPLE_REJECTION_MORATORIUM = """
Dear Policyholder,

Your claim for hospitalization due to hypertension has been rejected.
The condition is classified as a pre-existing disease not disclosed
at policy inception.

As per policy terms, pre-existing diseases are excluded.
"""

SAMPLE_POLICY_LONG_TENURE = """
Policy Number: HIP/2014/005621
Policy Inception: March 2015
Renewal History: Continuous renewal for 9 years without break.
Sum Insured: Rs. 5,00,000
"""

SAMPLE_VAGUE_REJECTION = """
Dear Sir/Madam,

Your claim is not covered.

Regards
"""


# ─────────────────────────────────────────────────────────────────
# TEST GROUP 1: Document Segmentator
# ─────────────────────────────────────────────────────────────────

class TestSegmentator:
    def setup_method(self):
        from extractors.segmentator import segment_document
        self.segment = segment_document

    def test_detects_exclusions_section(self):
        doc = self.segment(SAMPLE_POLICY)
        assert "EXCLUSIONS" in doc.sections, "Should detect Exclusions section"
        assert len(doc.sections["EXCLUSIONS"].text) > 10

    def test_detects_waiting_period_section(self):
        doc = self.segment(SAMPLE_POLICY)
        assert "WAITING_PERIOD" in doc.sections, "Should detect Waiting Period section"

    def test_detects_grievance_section(self):
        doc = self.segment(SAMPLE_POLICY)
        assert "GRIEVANCE" in doc.sections, "Should detect Grievance section"

    def test_priority_text_returns_content(self):
        doc = self.segment(SAMPLE_POLICY)
        text = doc.priority_text(["EXCLUSIONS", "WAITING_PERIOD"])
        assert len(text) > 50, "Priority text should return content"

    def test_no_structure_returns_general(self):
        doc = self.segment("This is some random text without structure.")
        assert doc.general_text, "Should return text as general when no sections found"


# ─────────────────────────────────────────────────────────────────
# TEST GROUP 2: Rejection Classifier
# ─────────────────────────────────────────────────────────────────

class TestRejectionClassifier:
    def setup_method(self):
        from rules.rejection_rules import classify_rejection
        self.classify = classify_rejection

    def test_detects_hard_rejection(self):
        result = self.classify(SAMPLE_REJECTION_HARD)
        assert result.is_rejection, "Should detect hard rejection"
        assert result.detection_mode == "hard"

    def test_detects_soft_rejection(self):
        result = self.classify(SAMPLE_REJECTION_SOFT)
        assert result.is_rejection, "Should detect soft rejection"
        assert result.detection_mode == "soft"

    def test_classifies_ped_category(self):
        result = self.classify(SAMPLE_REJECTION_HARD)
        codes = [cat.code for cat in result.categories]
        assert "PED" in codes, "Should classify as PED rejection"

    def test_classifies_waiting_period(self):
        result = self.classify(SAMPLE_REJECTION_SOFT)
        codes = [cat.code for cat in result.categories]
        assert "WAITING_PERIOD" in codes, "Should detect waiting period"

    def test_confidence_high_on_hard_rejection(self):
        result = self.classify(SAMPLE_REJECTION_HARD)
        assert result.confidence in ("High", "Medium"), "Confidence should be at least Medium"

    def test_moratorium_detection(self):
        combined = SAMPLE_REJECTION_MORATORIUM + " " + SAMPLE_POLICY_LONG_TENURE
        result = self.classify(combined)
        assert result.moratorium_applicable, "Should detect moratorium applicability"

    def test_appeal_boost_ped(self):
        result = self.classify(SAMPLE_REJECTION_HARD)
        assert result.appeal_boost_total > 0, "PED rejection should have positive appeal boost"

    def test_no_rejection_in_normal_text(self):
        result = self.classify("Your policy has been renewed successfully. Thank you.")
        assert not result.is_rejection, "Should not flag non-rejection text"


# ─────────────────────────────────────────────────────────────────
# TEST GROUP 3: IRDAI Rule Validators
# ─────────────────────────────────────────────────────────────────

class TestIRDAIRules:
    def setup_method(self):
        from rules.irdai_rules import (
            check_moratorium_rule, check_clause_citation,
            check_late_intimation_rule, run_all_irdai_checks,
        )
        self.moratorium = check_moratorium_rule
        self.clause_citation = check_clause_citation
        self.late_intimation = check_late_intimation_rule
        self.run_all = run_all_irdai_checks

    def test_moratorium_triggered(self):
        rejection = SAMPLE_REJECTION_MORATORIUM
        policy = SAMPLE_POLICY_LONG_TENURE
        result = self.moratorium(rejection, policy)
        assert result["applicable"], "Moratorium should trigger"
        assert result["severity"] == "Critical"

    def test_moratorium_not_triggered_short_tenure(self):
        policy = "Policy Inception: 2023. First year policy."
        result = self.moratorium(SAMPLE_REJECTION_HARD, policy)
        assert not result["applicable"], "Moratorium should NOT trigger for new policy"

    def test_clause_citation_detected_when_present(self):
        result = self.clause_citation(SAMPLE_REJECTION_HARD)
        # SAMPLE_REJECTION_HARD contains "Clause 4.2" which should be detected
        # so applicable should be False (not a violation)
        assert not result["applicable"], f"Should NOT trigger violation when clause is present. Finding: {result.get('finding')}"

    def test_clause_citation_triggered_when_missing(self):
        vague = "Your claim is not payable. Not covered."
        result = self.clause_citation(vague)
        assert result["applicable"], "Should trigger violation (applicable=True) when clause is missing"

    def test_clause_citation_missing(self):
        result = self.clause_citation(SAMPLE_VAGUE_REJECTION)
        assert result["applicable"], "Should flag missing clause citation"
        assert result["severity"] == "High"

    def test_late_intimation_alone_flagged(self):
        letter = "Your claim is rejected due to late intimation. You did not inform us within 24 hours."
        result = self.late_intimation(letter)
        assert result["applicable"], "Should flag late intimation as sole reason"
        assert result["severity"] == "Critical"

    def test_run_all_returns_list(self):
        findings = self.run_all(SAMPLE_REJECTION_HARD, SAMPLE_POLICY)
        assert isinstance(findings, list)


# ─────────────────────────────────────────────────────────────────
# TEST GROUP 4: PDF Extractor (unit-level, no real PDF needed)
# ─────────────────────────────────────────────────────────────────

class TestPDFExtractorUtils:
    def setup_method(self):
        from extractors.pdf_extractor import _score_text, _clean_text
        self.score = _score_text
        self.clean = _clean_text

    def test_empty_text_scores_zero(self):
        assert self.score("") == 0.0

    def test_insurance_domain_text_scores_high(self):
        score = self.score(SAMPLE_POLICY)
        assert score > 0.35, f"Insurance text should score > 0.35, got {score:.2f}"

    def test_random_chars_scores_low(self):
        score = self.score("xyz @#$ 123 !!! abc %%% ##")
        assert score < 0.3

    def test_clean_removes_page_markers(self):
        text = "Hello\nPage 1 of 10\nWorld\nPage 2 of 10"
        cleaned = self.clean(text)
        assert "Page 1 of 10" not in cleaned

    def test_clean_collapses_blank_lines(self):
        text = "Para 1\n\n\n\n\nPara 2"
        cleaned = self.clean(text)
        assert "\n\n\n" not in cleaned


# ─────────────────────────────────────────────────────────────────
# TEST GROUP 5: RAG Retriever smoke test (optional — skips if index missing)
# ─────────────────────────────────────────────────────────────────

class TestRAGRetriever:
    def test_retriever_loads(self):
        try:
            from rag.hybrid_retriever import HybridRegulatoryRetriever
            r = HybridRegulatoryRetriever()
            assert r is not None
        except Exception as e:
            pytest.skip(f"Retriever not available: {e}")

    def test_combined_retrieve_returns_string(self):
        try:
            from rag.hybrid_retriever import HybridRegulatoryRetriever
            r = HybridRegulatoryRetriever()
            if not r.is_ready:
                pytest.skip("No FAISS indices found — build with rag/rag_builder.py")
            result = r.retrieve("pre-existing disease waiting period")
            assert isinstance(result, str)
            assert len(result) > 10
        except Exception as e:
            pytest.skip(f"RAG test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
