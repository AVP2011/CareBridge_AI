SCORING_CONFIG = {

    # -------------------------------------------------------
    # Base score — deductions and boosts applied from here
    # -------------------------------------------------------
    "base_score": 80,   # Set to 80; allows clean offset with boosts up to 100 for premium policies

    # -------------------------------------------------------
    # IRDAI compliance boost — max points for full compliance
    # Normalised against compliance_scale in scoring engine
    # -------------------------------------------------------
    "compliance_max_boost": 10.0,  # Compliance acts as a positive signaller, capped at +10
    "compliance_scale": 7.0,

    # -------------------------------------------------------
    # Systemic risk penalty — applied when majority of fields are High Risk
    # -------------------------------------------------------
    "majority_high_risk_penalty": -15.0,

    # -------------------------------------------------------
    # Score band thresholds (used by engine for rating)
    # -------------------------------------------------------
    "rating_thresholds": {
        "Strong": 80.0,
        "Moderate": 55.0,
        # below Moderate = "Weak"
    },

    # -------------------------------------------------------
    # Precise, clause-by-clause weights, penalties, and boosts
    # -------------------------------------------------------
    "clauses": {
        "room_rent_sublimit": {
            "name": "Room Rent Sublimit",
            "weight_class": "Critical Financial",
            "penalties": {
                "High Risk": -15.0,
                "Moderate Risk": -7.0,
                "Low Risk": 0.0,
                "Not Mentioned": -4.0,  # High risk of hidden sublimits triggering proportionate deductions
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 5.0  # Award premium cover for no cap room rent
            },
            "descriptions": {
                "High Risk": "A strict room rent cap limits claims for hospital room coverage",
                "Moderate Risk": "Room rent limit is moderate, but may still cap total payouts",
                "Low Risk": "No room rent sublimit protects against unexpected room charge cuts",
                "Not Mentioned": "Absence of room rent clause in documents poses a potential hidden sublimit risk",
                "Not Found": "No room rent details were successfully extracted from the policy text"
            }
        },
        "co_payment": {
            "name": "Co-payment",
            "weight_class": "Critical Financial",
            "penalties": {
                "High Risk": -15.0,
                "Moderate Risk": -8.0,
                "Low Risk": 0.0,
                "Not Mentioned": -2.0,  # Small precaution penalty
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 5.0  # Zero co-pay boost
            },
            "descriptions": {
                "High Risk": "High co-payment requirements will require significant out-of-pocket expenses",
                "Moderate Risk": "Moderate co-payment applies, typical for elder age brackets or specific zones",
                "Low Risk": "Nil co-payment coverage guarantees the insurer pays 100% of approved claims",
                "Not Mentioned": "No explicit co-payment is mentioned, leaving a slight ambiguity",
                "Not Found": "Co-payment clause was not detected in the extracted text"
            }
        },
        "pre_existing_disease": {
            "name": "Pre-Existing Disease Waiting Period",
            "weight_class": "Critical Financial",
            "penalties": {
                "High Risk": -12.0,
                "Moderate Risk": -6.0,
                "Low Risk": 0.0,
                "Not Mentioned": -4.0,  # Standard long exclusion might apply silently
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 4.0  # Short waiting period (1-2 years) reward
            },
            "descriptions": {
                "High Risk": "Long waiting period (4 years or more) for pre-existing disease claims",
                "Moderate Risk": "Standard 3-year waiting period for pre-existing diseases",
                "Low Risk": "Favorable short waiting period (1-2 years) for pre-existing diseases",
                "Not Mentioned": "Pre-existing disease clause not mentioned; standard default limits may apply",
                "Not Found": "Pre-existing disease details were not found in the policy"
            }
        },
        "disease_specific_caps": {
            "name": "Disease-Specific Caps",
            "weight_class": "Critical Financial",
            "penalties": {
                "High Risk": -12.0,
                "Moderate Risk": -6.0,
                "Low Risk": 0.0,
                "Not Mentioned": -3.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 4.0  # No disease caps boost
            },
            "descriptions": {
                "High Risk": "Specific limits on common treatments like cataracts/hernia can severely cut payouts",
                "Moderate Risk": "Moderate limits on specific surgeries are documented",
                "Low Risk": "Absence of disease-specific limits ensures claim settlement up to the sum insured",
                "Not Mentioned": "No disease caps mentioned, which may leave potential caps unverified",
                "Not Found": "Disease-specific limits were not extracted successfully"
            }
        },
        "waiting_period": {
            "name": "Waiting Period (General)",
            "weight_class": "Medium Financial",
            "penalties": {
                "High Risk": -10.0,
                "Moderate Risk": -4.0,
                "Low Risk": 0.0,
                "Not Mentioned": -2.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 3.0
            },
            "descriptions": {
                "High Risk": "Restrictive initial waiting period or long specific conditions wait times",
                "Moderate Risk": "Standard 30-day initial waiting period applies",
                "Low Risk": "Favorable waived or reduced waiting periods observed",
                "Not Mentioned": "General waiting periods are not explicitly specified in the document",
                "Not Found": "Waiting period clauses could not be located in the text"
            }
        },
        "sublimits_and_caps": {
            "name": "Sublimits and Caps (General)",
            "weight_class": "Medium Financial",
            "penalties": {
                "High Risk": -10.0,
                "Moderate Risk": -5.0,
                "Low Risk": 0.0,
                "Not Mentioned": -2.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 3.0
            },
            "descriptions": {
                "High Risk": "Severe sublimits on ICU, modern care, or hospitalization charges",
                "Moderate Risk": "Moderate sublimits or minor caps on sub-services apply",
                "Low Risk": "No overall sublimits provides full coverage flexibility",
                "Not Mentioned": "Sublimits and caps not mentioned, presenting moderate risk of hidden caps",
                "Not Found": "Sublimits data could not be parsed"
            }
        },
        "restoration_benefit": {
            "name": "Restoration Benefit",
            "weight_class": "Protective Benefit",
            "penalties": {
                "High Risk": -8.0,      # Poor trigger terms
                "Moderate Risk": -3.0,
                "Low Risk": 0.0,
                "Not Mentioned": -8.0,  # Implies no restoration benefit is provided
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 6.0  # Favorable restoration boost
            },
            "descriptions": {
                "High Risk": "No restoration benefit or highly limiting triggers (e.g. only once, unrelated illnesses)",
                "Moderate Risk": "Restoration triggers only upon complete sum insured exhaustion or for unrelated illnesses",
                "Low Risk": "Unlimited restoration / restoration on partial exhaustion protects family floaters",
                "Not Mentioned": "Policy does not offer or mention restoration benefits",
                "Not Found": "Restoration benefits clause not found in the extraction"
            }
        },
        "exclusions_clarity": {
            "name": "Exclusions Clarity",
            "weight_class": "Administrative / Disclosure",
            "penalties": {
                "High Risk": -5.0,
                "Moderate Risk": -2.0,
                "Low Risk": 0.0,
                "Not Mentioned": -1.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 2.0
            },
            "descriptions": {
                "High Risk": "Vague or non-standard exclusions can lead to unpredictable claim rejections",
                "Moderate Risk": "Standard non-medical exclusions are outlined",
                "Low Risk": "Exclusions are clearly listed and follow standardized parameters",
                "Not Mentioned": "Exclusions are not clearly defined in the policy document",
                "Not Found": "Exclusions clause could not be located in the text"
            }
        },
        "claim_procedure_complexity": {
            "name": "Claim Procedure Complexity",
            "weight_class": "Administrative / Disclosure",
            "penalties": {
                "High Risk": -5.0,
                "Moderate Risk": -2.0,
                "Low Risk": 0.0,
                "Not Mentioned": -1.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 2.0
            },
            "descriptions": {
                "High Risk": "Highly complex claims process or very brief submission windows (e.g. < 7 days)",
                "Moderate Risk": "Standard claims timeline (e.g. 15-30 days) and manual submission guidelines",
                "Low Risk": "Seamless cashless claims process at network hospitals",
                "Not Mentioned": "Claim submission process and timelines are not specified",
                "Not Found": "Claims procedure sections were not detected"
            }
        },
        "transparency_of_terms": {
            "name": "Transparency of Terms",
            "weight_class": "Administrative / Disclosure",
            "penalties": {
                "High Risk": -4.0,
                "Moderate Risk": -2.0,
                "Low Risk": 0.0,
                "Not Mentioned": -1.0,
                "Not Found": 0.0
            },
            "boosts": {
                "Low Risk": 2.0
            },
            "descriptions": {
                "High Risk": "Extremely complex legal wording or dense formatting obscures important conditions",
                "Moderate Risk": "Standard complexity policy structure and readability",
                "Low Risk": "Clear, plain English definitions and well-structured clauses promote high trust",
                "Not Mentioned": "Formatting and reference indexes are absent or insufficient",
                "Not Found": "Transparency index could not be graded"
            }
        }
    }
}