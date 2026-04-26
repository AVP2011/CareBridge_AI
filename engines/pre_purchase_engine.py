import json
import re
import os
from pathlib import Path

from services.prepurchase_rule_engine import extract_structured_features
from llm.prepurchase_prompt import prepurchase_risk_prompt
from llm.generation import generate
from services.prepurchase_scoring import compute_policy_score
from services.irdai_compliance_engine import evaluate_irdai_compliance
from services.broker_risk_engine import analyze_broker_risk
from services.known_providers_db import get_pre_extracted_clause_risk, get_pre_extracted_summary

from rag.retrievers import IRDAIRetriever, StandardClauseRetriever
from services.compliance_bridge import ComplianceBridge

from schemas.pre_purchase import (
    ClauseRiskAssessment,
    PrePurchaseReport,
    IRDAICompliance,
    PolicyScoreBreakdown,
    BrokerRiskAnalysis,
    AgentValidation,
    AgentClaim,
)

_NOT_FOUND_DEFAULTS = {
    "waiting_period":             "Not Found",
    "pre_existing_disease":       "Not Found",
    "room_rent_sublimit":         "Not Found",
    "disease_specific_caps":      "Not Found",
    "co_payment":                 "Not Found",
    "exclusions_clarity":         "Not Found",
    "claim_procedure_complexity": "Not Found",
    "sublimits_and_caps":         "Not Found",
    "restoration_benefit":        "Not Found",
    "transparency_of_terms":      "Not Found",
}


def _safe_json_parse(raw: str) -> dict | None:
    """Parse JSON safely — accepts partial dicts too."""
    if not raw or raw.strip() in ("{}", ""):
        return None
    try:
        result = json.loads(raw.strip())
        if isinstance(result, dict) and len(result) > 0:
            return result
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            result = json.loads(match.group(0))
            if isinstance(result, dict) and len(result) > 0:
                return result
        except Exception:
            pass
    return None


def _apply_deterministic_overrides(clause_risk: ClauseRiskAssessment, features: dict) -> None:
    """
    Apply rule-based overrides to clause_risk IN PLACE.
    Corrects LLM 'Not Found' errors using high-confidence regex patterns.
    """

    # ── Waiting Period ──────────────────────────────────────
    wait = features.get("waiting_period_years", 0)
    if wait >= 4:
        clause_risk.waiting_period = "High Risk"
    elif wait == 3:
        clause_risk.waiting_period = "High Risk"
    elif wait == 2:
        clause_risk.waiting_period = "Moderate Risk"
    elif wait == 1:
        clause_risk.waiting_period = "Low Risk"
    elif features.get("has_waiting_period") and clause_risk.waiting_period == "Not Found":
        clause_risk.waiting_period = "Moderate Risk"

    # ── Co-payment ──────────────────────────────────────────
    co_pay = features.get("co_payment_percentage", 0)
    if co_pay >= 20:
        clause_risk.co_payment = "High Risk"
    elif 10 <= co_pay < 20:
        clause_risk.co_payment = "Moderate Risk"
    elif 0 < co_pay < 10:
        clause_risk.co_payment = "Low Risk"
    elif features.get("co_payment") and clause_risk.co_payment == "Not Found":
        clause_risk.co_payment = "Moderate Risk"

    # ── Room Rent Sublimit ──────────────────────────────────
    room_pct = features.get("room_rent_percent", 0)
    if 0 < room_pct <= 1:
        clause_risk.room_rent_sublimit = "High Risk"
    elif room_pct == 2:
        clause_risk.room_rent_sublimit = "Moderate Risk"
    elif room_pct >= 3:
        clause_risk.room_rent_sublimit = "Low Risk"
    elif features.get("room_rent_cap") and clause_risk.room_rent_sublimit == "Not Found":
        clause_risk.room_rent_sublimit = "Moderate Risk"

    # ── Pre-existing Disease ────────────────────────────────
    if features.get("mentions_pre_existing") and clause_risk.pre_existing_disease == "Not Found":
        clause_risk.pre_existing_disease = "Moderate Risk"

    # ── Disease Caps / Sublimits ────────────────────────────
    if features.get("disease_caps"):
        if clause_risk.disease_specific_caps == "Not Found":
            clause_risk.disease_specific_caps = "Moderate Risk"
        if clause_risk.sublimits_and_caps == "Not Found":
            clause_risk.sublimits_and_caps = "Moderate Risk"

    # ── Restoration Benefit ─────────────────────────────────
    if features.get("restoration_benefit") and clause_risk.restoration_benefit == "Not Found":
        clause_risk.restoration_benefit = "Low Risk"

    # ── Claim Procedure Complexity ──────────────────────────
    if features.get("procedural_conditions") and clause_risk.claim_procedure_complexity == "Not Found":
        clause_risk.claim_procedure_complexity = "Moderate Risk"

    # ── Exclusions Clarity ──────────────────────────────────
    if features.get("consumables_exclusion") and clause_risk.exclusions_clarity == "Not Found":
        clause_risk.exclusions_clarity = "High Risk"

    # ── Transparency ────────────────────────────────────────
    compliance_signals = sum([
        features.get("free_look_period", False),
        features.get("grievance_redressal", False),
        features.get("ombudsman_reference", False),
        features.get("irdai_reference", False),
    ])
    if compliance_signals >= 3 and clause_risk.transparency_of_terms == "Not Found":
        clause_risk.transparency_of_terms = "Low Risk"
    elif compliance_signals >= 1 and clause_risk.transparency_of_terms == "Not Found":
        clause_risk.transparency_of_terms = "Moderate Risk"


class PrePurchaseEngine:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.bridge = ComplianceBridge()
        
        # Initialize RAG Components
        rag_dir = os.path.join(Path(__file__).parent.parent, "rag", "indices")
        try:
            self.irdai_retriever = IRDAIRetriever(rag_dir)
            self.standard_retriever = StandardClauseRetriever(rag_dir)
            print("✅ PrePurchaseEngine: Retrievers active.")
        except Exception as e:
            print(f"⚠ PrePurchaseEngine: RAG init skipped ({e}).")
            self.irdai_retriever = None
            self.standard_retriever = None

    def run(self, policy_text: str, provider_id: str = None, agent_summary: str = None) -> PrePurchaseReport:
        # ─────────────────────────────────────────────────────
        # 0️⃣ PRE-EXTRACTED PROVIDER OVERRIDE
        # ─────────────────────────────────────────────────────
        if provider_id and provider_id != "Other providers":
            from services.known_providers_db import get_pre_extracted_clause_risk, get_pre_extracted_summary
            pre_extracted = get_pre_extracted_clause_risk(provider_id)
            
            if pre_extracted:
                clause_risk = ClauseRiskAssessment(**pre_extracted)
                summary = get_pre_extracted_summary(provider_id)
                compliance_dict = evaluate_irdai_compliance("").model_dump() # dummy empty string since not needed
                
                broker_risk_analysis = BrokerRiskAnalysis(
                    **analyze_broker_risk(clause_risk=clause_risk, compliance_data=compliance_dict)
                )

                score_data = compute_policy_score(clause_risk, compliance_dict) or {}
                score = float(score_data.get("adjusted_score", 65))
                rating = "Strong" if score >= 80 else "Moderate" if score >= 55 else "Weak"
                
                # Check agent validation since agent_summary might be provided
                agent_val = None
                if agent_summary:
                    prompt = prepurchase_risk_prompt(
                        policy_text="Pre-extracted clauses used. Do not read policy text, just validate agent_summary against standard typical policies.",
                        irdai_context="",
                        market_standards="",
                        agent_summary=agent_summary
                    )
                    raw_output = generate(prompt, self.model, self.tokenizer, json_mode=True, max_new_tokens=600)
                    parsed = _safe_json_parse(raw_output)
                    if parsed and "agent_validation" in parsed:
                        av_data = parsed["agent_validation"]
                        raw_claims = av_data.get("claims", [])
                        claims = []
                        for c in raw_claims:
                            cit = c.get("citation") or c.get("source_citation")
                            claims.append(AgentClaim(
                                claim=c.get("claim", ""),
                                fact_check=c.get("fact_check", ""),
                                is_correct=c.get("is_correct", False),
                                citation=cit
                            ))
                        agent_val = AgentValidation(
                            is_consistent=av_data.get("is_consistent", True),
                            verified_claims=[c for c in claims if c.is_correct][:3],
                            discrepancies=[c for c in claims if not c.is_correct][:4],
                            trust_score=av_data.get("trust_score", 100.0)
                        )
                        if agent_val.trust_score < 40: score -= 15
                        elif agent_val.trust_score < 75: score -= 5
                
                score = max(0.0, min(score, 100.0))
                rating = "Strong" if score >= 80 else "Moderate" if score >= 55 else "Weak"

                checklist = [
                    "Confirm the waiting period verbally with the agent.",
                    "Check for disease-specific sublimits in the policy schedule.",
                    "Verify restoration benefit triggers."
                ]
                
                # Fill regulatory citations
                reg_citations = []
                for clause_key, risk_val in clause_risk.model_dump().items():
                    if risk_val in ["High Risk", "Moderate Risk"]:
                        match = self.bridge.map_to_standard(clause_key)
                        if match:
                            reg_citations.append(f"{match['standard_label']}: {match['regulation_ref']}")

                return PrePurchaseReport(
                    clause_risk=clause_risk,
                    score_breakdown=PolicyScoreBreakdown(
                        base_score=score_data.get("base_score", score),
                        adjusted_score=score,
                        rating=rating,
                        risk_index=score_data.get("risk_index", 0.5),
                    ),
                    overall_policy_rating=rating,
                    summary=summary,
                    checklist_for_buyer=checklist,
                    confidence="High",
                    irdai_compliance=evaluate_irdai_compliance(""),
                    broker_risk_analysis=broker_risk_analysis,
                    agent_validation=agent_val,
                    regulatory_citations=list(dict.fromkeys(reg_citations))[:5],
                    red_flags=list(dict.fromkeys(score_data.get("red_flags", [])))[:3],
                    positive_flags=list(dict.fromkeys(score_data.get("positive_flags", [])))[:3],
                )

        # ─────────────────────────────────────────────────────
        # 1️⃣ RAG Data Gathering
        # ─────────────────────────────────────────────────────
        irdai_context = ""
        market_context = ""
        
        if self.irdai_retriever:
            all_irdai = []
            queries = ["waiting periods", "standard exclusions", "agent conduct circular"]
            for q in queries:
                all_irdai.extend(self.irdai_retriever.retrieve(q, k=2))
            
            irdai_snippets = []
            seen = set()
            for r in all_irdai:
                if r['text'][:50] not in seen:
                    irdai_snippets.append(f"[{r['source']}]: {r['text']}")
                    seen.add(r['text'][:50])
            irdai_context = "\n\n".join(irdai_snippets[:5])

        if self.standard_retriever:
            market_results = self.standard_retriever.retrieve(policy_text[:500], k=3)
            market_context = "\n\n".join([f"[{r['metadata']['insurer']}]: {r['text']}" for r in market_results])

        # ─────────────────────────────────────────────────────
        # 2️⃣ CLEAN & SCAN (Smart 3-Point Sampling)
        # Instead of first 8k, we take Start (10k), Middle (8k), and Last (5k)
        # to ensure we capture Benefits, Exclusions, and Procedures.
        full_text_clean = re.sub(r"\s+", " ", policy_text).strip()
        total_len = len(full_text_clean)
        
        if total_len <= 25000:
            policy_text_sampled = full_text_clean
        else:
            # 3-Point Sampling Logic
            head = full_text_clean[:10000]
            last = full_text_clean[-5000:]
            
            # Find the middle point and take a slice
            mid_start = (total_len // 2) - 5000
            mid_end   = (total_len // 2) + 5000
            middle = full_text_clean[mid_start:mid_end]
            
            policy_text_sampled = (
                f"[START SECTION]\n{head}\n\n"
                f"[MIDDLE SECTION (EXCLUSIONS)]\n{middle}\n\n"
                f"[END SECTION (CLAIMS & TERMS)]\n{last}"
            )

        features = extract_structured_features(policy_text_sampled)

        # 3️⃣ HYBRID GENERATION
        # ─────────────────────────────────────────────────────
        prompt = prepurchase_risk_prompt(
            policy_text=policy_text_sampled,
            irdai_context=irdai_context,
            market_standards=market_context,
            agent_summary=agent_summary
        )

        raw_output = generate(prompt, self.model, self.tokenizer, json_mode=True, max_new_tokens=1000)
        parsed = _safe_json_parse(raw_output)

        # ─────────────────────────────────────────────────────
        # 4️⃣ STRUCTURE & OVERRIDE
        # ─────────────────────────────────────────────────────
        risk_data = parsed.get("clause_risk", {}) if parsed else _NOT_FOUND_DEFAULTS
        _VALID = {"High Risk", "Moderate Risk", "Low Risk", "Not Found"}
        for key in _NOT_FOUND_DEFAULTS:
            val = risk_data.get(key, "Not Found")
            risk_data[key] = val if val in _VALID else "Not Found"
            
        clause_risk = ClauseRiskAssessment(**risk_data)
        _apply_deterministic_overrides(clause_risk, features)

        # Agent Validation Logic
        agent_val = None
        if agent_summary and parsed and "agent_validation" in parsed:
            av_data = parsed["agent_validation"]
            raw_claims = av_data.get("claims", [])
            claims = []
            for c in raw_claims:
                # Legacy fallback: accept 'source_citation' or 'citation'
                cit = c.get("citation") or c.get("source_citation")
                claims.append(AgentClaim(
                    claim=c.get("claim", ""),
                    fact_check=c.get("fact_check", ""),
                    is_correct=c.get("is_correct", False),
                    citation=cit
                ))
            
            # Compression: Cap discrepancies and verified claims
            discrepancies = [c for c in claims if not c.is_correct]
            verified = [c for c in claims if c.is_correct]
            
            agent_val = AgentValidation(
                is_consistent=av_data.get("is_consistent", True),
                verified_claims=verified[:3], # Cap to 3
                discrepancies=discrepancies[:4], # Cap to 4
                trust_score=av_data.get("trust_score", 100.0)
            )

        # ─────────────────────────────────────────────────────
        # 5️⃣ FINAL SCORING & COMPRESSION
        # ─────────────────────────────────────────────────────
        irdai_compliance_obj = evaluate_irdai_compliance(policy_text_sampled)
        compliance_dict = irdai_compliance_obj.model_dump()
        
        broker_risk_analysis = BrokerRiskAnalysis(
            **analyze_broker_risk(clause_risk=clause_risk, compliance_data=compliance_dict)
        )

        score_data = compute_policy_score(clause_risk, compliance_dict) or {}
        score = float(score_data.get("adjusted_score", 50))
        
        if agent_val:
            if agent_val.trust_score < 40: score -= 15
            elif agent_val.trust_score < 75: score -= 5
            
        score = max(0.0, min(score, 100.0))
        rating = "Strong" if score >= 80 else "Moderate" if score >= 55 else "Weak"

        # Compression: Deduplicate and Cap Flags
        red_flags = list(dict.fromkeys(score_data.get("red_flags", [])))[:3]
        pos_flags = list(dict.fromkeys(score_data.get("positive_flags", [])))[:3]
        
        # Capture regulatory citations
        reg_citations = parsed.get("regulatory_citations", []) if parsed else []
        
        # Bridge Augmentation: Auto-add citations based on detected risks
        for clause_key, risk_val in clause_risk.model_dump().items():
            if risk_val in ["High Risk", "Moderate Risk"]:
                match = self.bridge.map_to_standard(clause_key)
                if match:
                    reg_citations.append(f"{match['standard_label']}: {match['regulation_ref']}")

        reg_citations = list(dict.fromkeys([c for c in reg_citations if c]))[:5] # Cap to 5

        # Checklist normalization
        checklist = parsed.get("checklist_for_buyer", []) if parsed else []
        if not checklist:
            checklist = [
                "Confirm the waiting period verbally with the agent.",
                "Check for disease-specific sublimits in the policy schedule.",
                "Verify restoration benefit triggers."
            ]
        checklist = list(dict.fromkeys(checklist))[:4] # Cap to 4

        return PrePurchaseReport(
            clause_risk=clause_risk,
            score_breakdown=PolicyScoreBreakdown(
                base_score=score_data.get("base_score", score),
                adjusted_score=score,
                rating=rating,
                risk_index=score_data.get("risk_index", 0.5),
            ),
            overall_policy_rating=rating,
            summary=f"Analysis completed using IRDAI RAG + Agent Fact-Check validation.",
            checklist_for_buyer=checklist,
            confidence="High" if self.irdai_retriever else "Medium",
            irdai_compliance=irdai_compliance_obj,
            broker_risk_analysis=broker_risk_analysis,
            agent_validation=agent_val,
            regulatory_citations=reg_citations,
            red_flags=red_flags,
            positive_flags=pos_flags,
        )
