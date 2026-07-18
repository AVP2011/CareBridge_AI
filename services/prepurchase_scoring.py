from config.prepurchase_scoring_config import SCORING_CONFIG


def compute_policy_score(clause_risk, compliance_data: dict) -> dict:
    """
    Compute a 0-100 policy score with full explainability.
    
    Consumes precise, clause-specific weights and thresholds.
    """

    base_score = float(SCORING_CONFIG.get("base_score", 80))
    current_score = base_score

    deductions = []
    additions = []
    red_flags = []
    positive_flags = []
    high_risk_count = 0

    clauses_config = SCORING_CONFIG.get("clauses", {})

    # Evaluate each clause individually using configured weights
    for field_name, config in clauses_config.items():
        # Get actual risk grade from clause_risk output (fallback to "Not Found")
        risk_level = getattr(clause_risk, field_name, "Not Found")
        if risk_level not in ["High Risk", "Moderate Risk", "Low Risk", "Not Found", "Not Mentioned"]:
            risk_level = "Not Found"

        # 1. Look up penalty or boost
        penalties = config.get("penalties", {})
        boosts = config.get("boosts", {})
        descriptions = config.get("descriptions", {})

        penalty = float(penalties.get(risk_level, 0.0))
        boost = float(boosts.get(risk_level, 0.0))

        clause_friendly_name = config.get("name", field_name.replace("_", " ").title())

        # Apply negative penalty (if any)
        if penalty < 0:
            current_score += penalty
            spec_desc = descriptions.get(risk_level, f"Penalized due to {risk_level}")
            deductions.append({
                "source": clause_friendly_name,
                "impact": penalty,
                "description": spec_desc
            })
            if risk_level == "High Risk":
                red_flags.append(f"{clause_friendly_name}: {spec_desc}")
                high_risk_count += 1
            elif risk_level == "Not Mentioned" and penalty <= -4.0:
                # Treat heavy "Not Mentioned" clauses (like restoration or room rent) as warnings too
                red_flags.append(f"{clause_friendly_name}: {spec_desc}")

        # Apply positive boost (if any)
        if boost > 0:
            current_score += boost
            spec_desc = descriptions.get(risk_level, "Favorable clause detected")
            additions.append({
                "source": clause_friendly_name,
                "impact": boost,
                "description": spec_desc
            })
            positive_flags.append(f"{clause_friendly_name}: {spec_desc}")

    # 2. Compliance Boost
    compliance_boost = 0.0
    if compliance_data:
        raw_compliance = compliance_data.get("compliance_score", 0)
        compliance_scale = SCORING_CONFIG.get("compliance_scale", 7.0)
        max_boost = float(SCORING_CONFIG.get("compliance_max_boost", 10.0))
        
        # normalized 0-1
        normalized = max(0.0, min(float(raw_compliance) / compliance_scale, 1.0))
        compliance_boost = normalized * max_boost
        
        if compliance_boost > 0:
            current_score += compliance_boost
            additions.append({
                "source": "IRDAI Compliance",
                "impact": round(compliance_boost, 2),
                "description": f"Based on regulatory compliance score of {raw_compliance}/{compliance_scale}"
            })

    # 3. Systemic Risk Penalty
    total_fields = len(clauses_config)
    if total_fields > 0 and (high_risk_count / total_fields) >= 0.6:
        extra_penalty = float(SCORING_CONFIG.get("majority_high_risk_penalty", -15.0))
        current_score += extra_penalty
        deductions.append({
            "source": "Systemic Risk Factor",
            "impact": extra_penalty,
            "description": "High concentration of high-risk clauses indicates severe consumer financial exposure."
        })
        red_flags.append("Systemic risk: Multiple critical clauses carry High Risk protections.")

    # Bound final score to [0 - 100]
    final_score = max(0.0, min(100.0, current_score))
    # Risk index is inverse of final score scale
    risk_index = round((100.0 - final_score) / 100.0, 2)

    # Build Explainability reasoning text
    total_deductions = round(sum(d['impact'] for d in deductions), 2)
    total_additions = round(sum(a['impact'] for a in additions), 2)
    reasoning = (
        f"Score starts at a baseline of {base_score}. "
        f"Subtracted {abs(total_deductions)} points for identified policy limitations. "
        f"Added {total_additions} points for favorable benefits and compliance. "
        f"Final calculated policy rating score: {round(final_score, 1)}."
    )

    return {
        "base_score": base_score,
        "adjusted_score": round(final_score, 2),
        "risk_index": risk_index,
        "red_flags": red_flags,
        "positive_flags": positive_flags,
        "high_risk_count": high_risk_count,
        "explainability": {
            "base_score": base_score,
            "deductions": deductions,
            "additions": additions,
            "compliance_contribution": round(compliance_boost, 2),
            "final_score": round(final_score, 2),
            "reasoning": reasoning
        }
    }