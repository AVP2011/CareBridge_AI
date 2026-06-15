from config.prepurchase_scoring_config import SCORING_CONFIG


def compute_policy_score(clause_risk, compliance_data: dict) -> dict:
    """
    Compute a 0-100 policy score with full explainability.
    """

    base_score = float(SCORING_CONFIG["base_score"])
    current_score = base_score

    deductions = []
    additions = []
    red_flags = []
    positive_flags = []
    high_risk_count = 0

    financial_weights = SCORING_CONFIG["financial_weights"]
    financial_fields = SCORING_CONFIG["financial_fields"]

    # 1. Deductions (Financial Risk)
    for field_name in financial_fields:
        field_value = getattr(clause_risk, field_name, "Not Found")
        penalty = float(financial_weights.get(field_value, 0))
        
        if penalty < 0:
            current_score += penalty
            deductions.append({
                "source": field_name.replace("_", " ").title(),
                "impact": penalty,
                "description": f"Penalized due to {field_value}"
            })
            if field_value == "High Risk":
                red_flags.append(f"{field_name} marked as High Risk.")
                high_risk_count += 1

    # 2. Additions (Positive Boost)
    for field_name, boost_value in SCORING_CONFIG["positive_boost"].items():
        field_value = getattr(clause_risk, field_name, "Not Found")
        if field_value == "Low Risk":
            current_score += float(boost_value)
            additions.append({
                "source": field_name.replace("_", " ").title(),
                "impact": float(boost_value),
                "description": "Favorable clause detected"
            })
            positive_flags.append(f"{field_name} is favorable.")

    # 3. Compliance Boost
    compliance_boost = 0.0
    if compliance_data:
        raw_compliance = compliance_data.get("compliance_score", 0)
        compliance_scale = SCORING_CONFIG.get("compliance_scale", 7)
        max_boost = float(SCORING_CONFIG["compliance_max_boost"])
        # normalised 0-1
        normalised = max(0.0, min(float(raw_compliance) / compliance_scale, 1.0))
        compliance_boost = normalised * max_boost
        
        if compliance_boost > 0:
            current_score += compliance_boost
            additions.append({
                "source": "IRDAI Compliance",
                "impact": round(compliance_boost, 2),
                "description": f"Based on compliance score {raw_compliance}/{compliance_scale}"
            })

    # 4. Systemic Risk Penalty
    total_fields = len(financial_fields)
    if total_fields > 0 and high_risk_count / total_fields >= 0.6:
        extra_penalty = float(SCORING_CONFIG.get("majority_high_risk_penalty", -10))
        current_score += extra_penalty
        deductions.append({
            "source": "Systemic Risk",
            "impact": extra_penalty,
            "description": "High concentration of high-risk clauses"
        })
        red_flags.append("Systemic risk due to majority high-risk clauses.")

    final_score = max(0.0, min(100.0, current_score))
    risk_index = round((100.0 - final_score) / 100.0, 2)

    # Build Explainability reasoning
    reasoning = (
        f"Score starts at {base_score}. "
        f"Deducted {sum(d['impact'] for d in deductions)} for risks. "
        f"Added {sum(a['impact'] for a in additions)} for favorable terms and compliance. "
        f"Final capped score: {final_score}."
    )

    return {
        "base_score": base_score,
        "adjusted_score": final_score,
        "risk_index": risk_index,
        "red_flags": red_flags,
        "positive_flags": positive_flags,
        "high_risk_count": high_risk_count,
        "explainability": {
            "base_score": base_score,
            "deductions": deductions,
            "additions": additions,
            "compliance_contribution": round(compliance_boost, 2),
            "final_score": final_score,
            "reasoning": reasoning
        }
    }