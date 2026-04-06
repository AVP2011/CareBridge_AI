def extract_structured_features(policy_text: str):
    """
    Extract deterministic insurance policy features
    for risk overrides and scoring.

    Improved keyword coverage.
    """

    text = policy_text.lower()

    features = {
        # Waiting Period
        "has_waiting_period": "waiting period" in text,
        "waiting_period_years": (
            4 if "48 month" in text or "4 year" in text else
            3 if "36 month" in text or "3 year" in text else
            2 if "24 month" in text or "2 year" in text else
            1 if "12 month" in text or "1 year" in text else 0
        ),

        # Pre-existing disease
        "mentions_pre_existing": any(k in text for k in [
            "pre-existing",
            "pre existing",
            "preexisting"
        ]),

        # Room rent
        "room_rent_cap": "room rent" in text,
        "room_rent_percent": (
            1 if "1%" in text else
            2 if "2%" in text else
            3 if "3%" in text else 0
        ),

        # Co-payment
        "co_payment": any(k in text for k in [
            "co-pay",
            "copay",
            "co payment",
            "co-payment"
        ]),
        "co_payment_percentage": (
            30 if "30%" in text else
            25 if "25%" in text else
            20 if "20%" in text else
            10 if "10%" in text else 0
        ),

        # Disease caps / sublimits
        "disease_caps": any(k in text for k in [
            "capped",
            "cap at",
            "limited to",
            "limit per",
            "maximum payable",
            "sublimit",
            "sub-limit",
            "sublimits"
        ]),

        # Consumables
        "consumables_exclusion": any(k in text for k in [
            "non-medical",
            "consumables excluded",
            "ppe kit",
            "gloves",
            "administrative charges"
        ]),

        # Restoration benefit
        "restoration_benefit": any(k in text for k in [
            "restoration benefit",
            "sum insured will be restored",
            "restored once",
            "reinstated"
        ]),

        # Claim procedure complexity
        "procedural_conditions": any(k in text for k in [
            "pre-authorization",
            "pre authorization",
            "intimation within",
            "submitted within",
            "inform within",
            "documents within"
        ]),

        # Transparency & compliance
        "free_look_period": "free look" in text,
        "grievance_redressal": "grievance" in text,
        "ombudsman_reference": "ombudsman" in text,
        "irdai_reference": "irdai" in text,
    }

    try:
        from services.clause_extractor_comprehensive import ComprehensiveClauseExtractor
        extractor = ComprehensiveClauseExtractor()
        extracted_clauses = extractor.extract_all_clauses(policy_text)

        # Map to our override flags
        if "waiting_period" in extracted_clauses:
            features["has_waiting_period"] = True
            val = str(extracted_clauses["waiting_period"].value).lower()
            if "48" in val or "4 year" in val: features["waiting_period_years"] = 4
            elif "36" in val or "3 year" in val: features["waiting_period_years"] = 3
            elif "24" in val or "2 year" in val: features["waiting_period_years"] = 2
            else: features["waiting_period_years"] = 1
        
        if "pre_existing_disease" in extracted_clauses:
            features["mentions_pre_existing"] = True
        
        if "room_rent_limit" in extracted_clauses:
            features["room_rent_cap"] = True
            val = str(extracted_clauses["room_rent_limit"].value)
            if "%" in val:
                try:
                    pct = int(val.split("%")[0].strip())
                    features["room_rent_percent"] = pct
                except:
                    features["room_rent_percent"] = 1
                    
        if "co_payment" in extracted_clauses:
            features["co_payment"] = True
            val = str(extracted_clauses["co_payment"].value)
            if "%" in val:
                try:
                    pct = int(val.split("%")[0].strip())
                    features["co_payment_percentage"] = pct
                except:
                    pass

        if "sub_limits" in extracted_clauses:
            features["disease_caps"] = True

    except Exception as e:
        print(f"Warning: ComprehensiveClauseExtractor failed: {e}")

    return features