def prepurchase_risk_prompt(
    policy_text: str, 
    irdai_context: str = "", 
    market_standards: str = "",
    agent_summary: str = ""
) -> str:
    """
    Hybrid RAG Prompt for MedGemma.
    Integrates policy text with IRDAI regulations and market benchmarks.
    If agent_summary is provided, performs fact-check validation.
    """
    
    agent_task = ""
    if agent_summary:
        agent_task = f"""
        FACT-CHECK AGENT CLAIMS:
        The user was told this by their agent: "{agent_summary}"
        Compare these claims against the policy and IRDAI rules.
        Identify any lies, exaggerations, or discrepancies.
        """

    return f"""Analyze this health insurance policy. Compare it against IRDAI regulations and industry benchmarks.
Provide a concise, trust-worthy decision report. Focus on what matters most to a buyer.

{agent_task}

IRDAI REGULATORY CONTEXT:
{irdai_context if irdai_context else "Use standard IRDAI 2016/2019 guidelines."}

MARKET STANDARDS (Other similar policies):
{market_standards if market_standards else "Compare against Star/Niva Bupa/HDFC benchmarks."}

CONSTRAINTS:
1. BREVITY: Keep explanations short and buyer-friendly. Avoid legal jargon.
2. CAPPING: Max 3 key concerns, max 3 red flags, max 4 checklist items.
3. DEDUPLICATION: Do not repeat the same issue across multiple sections.
4. TONE: Professional, objective, and actionable.

OUTPUT SCHEMA (JSON only):
{{
  "clause_risk": {{
    "waiting_period": "RiskLevel",
    "pre_existing_disease": "RiskLevel",
    "room_rent_sublimit": "RiskLevel",
    "disease_specific_caps": "RiskLevel",
    "co_payment": "RiskLevel",
    "exclusions_clarity": "RiskLevel",
    "claim_procedure_complexity": "RiskLevel",
    "sublimits_and_caps": "RiskLevel",
    "restoration_benefit": "RiskLevel",
    "transparency_of_terms": "RiskLevel"
  }},
  "agent_validation": {{
    "is_consistent": boolean,
    "claims": [
       {{
         "claim": "string",
         "fact_check": "Concise evidence from policy/IRDAI",
         "is_correct": boolean,
         "citation": "Short regulatory section or policy page"
       }}
    ],
    "trust_score": float (0-100)
  }},
  "regulatory_citations": ["List of 3-5 relevant IRDAI sections"],
  "checklist_for_buyer": ["4 actionable next steps"],
  "positive_flags": ["Max 3 positive signals"],
  "red_flags": ["Max 3 critical red flags"]
}}

POLICY TEXT:
{policy_text}

JSON OUTPUT:"""