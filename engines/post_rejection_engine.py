import threading

from services.clause_matcher import run_clause_matcher
from services.documentation_analyzer import run_documentation_analysis
from services.scoring_engine import compute_appeal_strength
from services.report_builder import build_final_report

from rag.hybrid_retriever import HybridRegulatoryRetriever, get_retriever
from schemas.response import FinalReport, AppealStrength

from services.rule_engine import apply_rule_overrides, apply_waiting_period_override
from services.documentation_rule_engine import apply_documentation_overrides
from services.contradiction_engine import detect_preexisting_contradiction
from services.input_sanitizer import sanitize_audit_input
from services.confidence_calibrator import calibrate_confidence

try:
    from rules.rejection_rules import classify_rejection
    from rules.irdai_rules import run_all_irdai_checks, format_irdai_findings
    from rules.broker_risk_engine import BrokerRiskEngine
    _RULES_AVAILABLE = True
except ImportError:
    _RULES_AVAILABLE = False
    print("⚠️  rules/ package not found — running without deterministic rule layer")

# ✅ Retriever is a lazy singleton via get_retriever() in rag/hybrid_retriever.py
def _get_retriever() -> HybridRegulatoryRetriever:
    return get_retriever()


def _retrieve_with_timeout(
    retriever: HybridRegulatoryRetriever,
    rejection_text: str,
    timeout: int = 30,
) -> str:
    """Run RAG retrieval in a thread with timeout protection."""
    result = {"value": None, "error": None}

    def _run():
        try:
            result["value"] = retriever.retrieve(rejection_text)
        except Exception as e:
            result["error"] = e

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        print(f"⚠️ Regulatory retrieval timed out after {timeout}s")
        return "Regulatory references could not be retrieved (timeout)."

    if result["error"]:
        print("⚠️ Regulatory retrieval error:", result["error"])
        return "Regulatory references could not be retrieved."

    return result["value"] or "No relevant regulatory references found."


def _low_confidence_report(regulatory_context: str) -> FinalReport:
    """Return a safe fallback report when confidence is too low to proceed."""
    return FinalReport(
        case_summary=(
            "The system could not confidently interpret the claim rejection "
            "based on the provided documents."
        ),
        why_rejected=(
            "Insufficient clarity detected in insurer communication or policy text."
        ),
        policy_clause_detected="Unclear from provided documents",
        clause_alignment="Partial",
        weak_points=[
            "Low confidence in automated interpretation.",
            "Policy wording and rejection reasoning may require manual review.",
        ],
        strong_points=[],
        reapplication_steps=[
            "Request insurer to specify the exact policy clause applied.",
            "Request detailed written clarification of rejection reasoning.",
            "Consult an insurance advisor for manual review.",
        ],
        appeal_strength=AppealStrength(
            percentage=50,
            label="Moderate",
            reasoning=(
                "Low confidence in automated interpretation; "
                "score defaulted conservatively."
            ),
        ),
        regulatory_considerations=regulatory_context,
        confidence="Low",
        system_notice=(
            "Automated interpretation paused due to low confidence. "
            "Manual clarification is recommended."
        ),
    )


class PostRejectionEngine:
    """
    Full Post-Rejection Pipeline:

    0. Input Sanitization & Schema Validation
    1. Clause Matching (LLM)
    2. Contradiction Detection & Rule Overrides
    3. Documentation Analysis (LLM + overrides)
    4. Regulatory Retrieval (Hybrid RAG, timeout-protected)
    5. Safety Gate (confidence check)
    6. Deterministic Scoring
    7. Confidence Calibration
    8. Structured Final Report
    """

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        # ✅ Retriever is a lazy singleton — not loaded here

    def run(self, request) -> FinalReport:

        # --------------------------------------------------
        # STEP 0: Input Sanitization
        # --------------------------------------------------
        clean_input = sanitize_audit_input(request)

        if clean_input["input_quality"] == "Low":
            return _low_confidence_report(
                "Input quality too low to proceed — rejection text missing or policy text too short."
            )

        policy_text      = clean_input["policy_text"]
        rejection_text   = clean_input["rejection_text"]
        medical_text     = clean_input["medical_text"]
        user_explanation = clean_input["user_explanation"]

        # --------------------------------------------------
        # STEP 1a: Deterministic Rejection Classification
        # Runs BEFORE LLM — hard/soft pattern + 12-category detection
        # --------------------------------------------------
        rejection_analysis = None
        irdai_findings_str = ""

        if _RULES_AVAILABLE:
            rejection_analysis = classify_rejection(rejection_text, policy_text)
            print(f"  [rules] {rejection_analysis.summary()}")

            irdai_checks = run_all_irdai_checks(rejection_text, policy_text)
            irdai_findings_str = format_irdai_findings(irdai_checks)
            print(f"  [irdai] {len(irdai_checks)} regulatory findings")

        # --------------------------------------------------
        # STEP 1b: Clause Matching (LLM)
        # --------------------------------------------------
        clause_result = run_clause_matcher(
            self.model,
            self.tokenizer,
            policy_text,
            rejection_text,
            user_explanation,
        )

        # --------------------------------------------------
        # STEP 2: Logical Enhancements + Rule Overrides
        # --------------------------------------------------
        clause_result = apply_rule_overrides(clause_result, rejection_text)

        clause_result = detect_preexisting_contradiction(
            clause_result, policy_text, medical_text
        )

        clause_result = apply_waiting_period_override(
            clause_result, policy_text, medical_text
        )

        # --------------------------------------------------
        # STEP 3: Documentation Analysis
        # --------------------------------------------------
        doc_result = run_documentation_analysis(
            self.model,
            self.tokenizer,
            policy_text,
            rejection_text,
            medical_text,
            user_explanation,
        )

        doc_result = apply_documentation_overrides(doc_result, rejection_text)

        # --------------------------------------------------
        # STEP 4: Regulatory Retrieval (timeout-protected, dual RAG)
        # --------------------------------------------------
        retriever = _get_retriever()
        # Use targeted retrieval for rejection audit when possible
        primary_clause = (
            rejection_analysis.primary_category.label
            if rejection_analysis and rejection_analysis.primary_category
            else ""
        )
        try:
            regulatory_context = _retrieve_with_timeout(
                retriever,
                rejection_text + " " + primary_clause,
            )
        except Exception:
            regulatory_context = _retrieve_with_timeout(retriever, rejection_text)

        # Prepend IRDAI rule findings to regulatory context
        if irdai_findings_str:
            regulatory_context = irdai_findings_str + "\n\n" + regulatory_context

        # --------------------------------------------------
        # STEP 5: Safety Gate
        # --------------------------------------------------
        clause_low = clause_result.confidence == "Low"
        doc_low    = doc_result.confidence == "Low"

        if clause_low and doc_low:
            return _low_confidence_report(regulatory_context)

        if clause_low or doc_low:
            print("⚠️ Partial low confidence detected — proceeding with caution")

        # --------------------------------------------------
        # STEP 6: Deterministic Scoring
        # --------------------------------------------------
        appeal_strength_data = compute_appeal_strength(clause_result, doc_result)

        # --------------------------------------------------
        # STEP 7: Confidence Calibration
        # --------------------------------------------------
        final_confidence = calibrate_confidence(clause_result, doc_result)

        try:
            clause_result = clause_result.model_copy(
                update={"confidence": final_confidence}
            )
        except Exception:
            clause_result.confidence = final_confidence

        # --------------------------------------------------
        # STEP 7: Risk Analysis (Phase 4 Integration)
        # --------------------------------------------------
        risk_data = None
        if _RULES_AVAILABLE:
            try:
                risk_engine = BrokerRiskEngine()
                risk_data = risk_engine.analyze_misrepresentation(rejection_text, {})
                print(f"  [risk] Score: {risk_data['risk_score']} Level: {risk_data['risk_level']}")
            except Exception as e:
                print(f"  ⚠️ Risk Engine failed: {e}")

        # --------------------------------------------------
        # STEP 8: Structured Final Report
        # --------------------------------------------------
        final_report = build_final_report(
            clause_result=clause_result,
            doc_result=doc_result,
            appeal_strength_data=appeal_strength_data,
            regulatory_context=regulatory_context,
        )
        
        # Inject risk data
        if risk_data:
            from schemas.response import BrokerRiskData, RiskFactor
            final_report.risk_data = BrokerRiskData(
                risk_score=risk_data["risk_score"],
                risk_level=risk_data["risk_level"],
                action=risk_data["action"],
                factors=[RiskFactor(**f) for f in risk_data["factors"]]
            )

        return final_report