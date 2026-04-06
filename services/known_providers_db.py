import json

_RAW_PROVIDER_DATA = [
    {
        "insurer": "Niva Bupa",
        "policy_name": "RISE",
        "clauses": [
            {
                "title": "Pre-Existing Disease Waiting Period",
                "category": "Pre-existing Condition",
                "waiting_period_months": 36,
                "description": "Expenses related to pre-existing diseases are excluded until completion of 36 months of continuous coverage from policy start date."
            },
            {
                "title": "Specific Disease Waiting Period",
                "category": "Specific Condition Waiting Period",
                "waiting_period_months": 24,
                "description": "Certain listed medical conditions are excluded until completion of 24 months from policy start date."
            },
            {
                "title": "Initial 30-Day Waiting Period",
                "category": "Initial Waiting Period",
                "waiting_period_days": 30,
                "description": "Any illness occurring within 30 days from policy start date is excluded, except in case of accident."
            },
            {
                "title": "Investigation-Only Admission",
                "category": "Diagnostic-Only Hospitalization",
                "description": "Hospitalization solely for diagnostic or investigative purposes without active line of treatment is excluded."
            },
            {
                "title": "Cosmetic / Aesthetic Treatment Exclusion",
                "category": "Cosmetic Exclusion",
                "description": "Cosmetic or aesthetic treatments are excluded unless medically necessary due to illness or injury."
            },
            {
                "title": "Medical Necessity / Reasonable & Customary Charges",
                "category": "Medical Necessity",
                "description": "Claims may be rejected if treatment is not medically necessary or if charges are not reasonable and customary."
            },
            {
                "title": "Self-Inflicted Injury Exclusion",
                "category": "Intentional Injury",
                "description": "Treatment arising from intentional self-inflicted injury is excluded."
            },
            {
                "title": "Substance Abuse Exclusion",
                "category": "Alcohol / Drug Related",
                "description": "Treatment related to alcohol or substance abuse is excluded under policy terms."
            }
        ]
    },
    {
        "insurer": "Star Health",
        "policy_name": "Comprehensive Health Insurance",
        "clauses": [
            {
                "title": "Pre-Existing Disease Waiting Period",
                "category": "Pre-existing Condition",
                "waiting_period_months": 36,
                "description": "Pre-existing diseases are covered only after 36 months of continuous coverage from policy inception."
            },
            {
                "title": "Specific Disease Waiting Period",
                "category": "Specific Condition Waiting Period",
                "waiting_period_months": 24,
                "description": "Certain listed conditions are covered only after 24 months from the policy start date."
            },
            {
                "title": "Initial Waiting Period",
                "category": "Initial Waiting Period",
                "waiting_period_days": 30,
                "description": "Any illness occurring within the first 30 days of policy commencement is not covered, except for accidents."
            },
            {
                "title": "Medical Necessity Requirement",
                "category": "Medical Necessity",
                "description": "Hospitalization must be medically necessary. Claims may be denied if treatment is not clinically justified or charges are excessive."
            },
            {
                "title": "Diagnostic-Only Hospitalization",
                "category": "Diagnostic Admission",
                "description": "Hospitalization solely for diagnostic purposes without active line of treatment is excluded."
            },
            {
                "title": "Substance Abuse Exclusion",
                "category": "Alcohol / Drug Related",
                "description": "Claims arising due to alcohol or substance abuse are excluded under the policy."
            },
            {
                "title": "Self-Inflicted Injury Exclusion",
                "category": "Intentional Injury",
                "description": "Hospitalization due to intentional self-inflicted injury is excluded."
            },
            {
                "title": "Cosmetic / Aesthetic Procedure Exclusion",
                "category": "Cosmetic Exclusion",
                "description": "Cosmetic or aesthetic procedures are excluded unless medically necessary due to illness or injury."
            }
        ]
    },
    {
        "insurer": "Aditya Birla Health Insurance",
        "product_name": "Activ Assure",
        "clauses": [
            {
                "category": "Waiting Period",
                "title": "30 Day Initial Waiting Period",
                "trigger": "Any illness occurring within 30 days of policy inception"
            },
            {
                "category": "Waiting Period",
                "title": "24 Month Specific Disease Waiting Period"
            },
            {
                "category": "Pre-Existing Disease",
                "title": "Pre-Existing Disease Waiting Period",
                "trigger": "Condition diagnosed within 48 months prior to policy start"
            },
            {
                "category": "Waiting Period",
                "title": "Genetic Disorder Waiting Period"
            },
            {
                "category": "Permanent Exclusion",
                "title": "Cosmetic and Aesthetic Procedures"
            },
            {
                "category": "Non-Medical Expense",
                "title": "Non-Medical Consumables"
            },
            {
                "category": "Financial Condition",
                "title": "Room Rent Proportionate Deduction"
            }
        ]
    },
    {
        "insurer": "HDFC ERGO",
        "product_name": "Health Suraksha / Optima Restore (Generic Comprehensive Plan Structure)",
        "clauses": [
            {
                "category": "Waiting Period",
                "title": "30 Day Initial Waiting Period"
            },
            {
                "category": "Pre-Existing Disease",
                "title": "Pre-Existing Disease Waiting Period",
                "waiting_period_months": 36
            },
            {
                "category": "Waiting Period",
                "title": "Specific Disease Waiting Period",
                "waiting_period_months": 24
            },
            {
                "category": "Medical Necessity",
                "title": "Medical Necessity Clause"
            },
            {
                "category": "Diagnostic Admission",
                "title": "Hospitalization for Investigation Only"
            },
            {
                "category": "Permanent Exclusion",
                "title": "Cosmetic / Aesthetic Treatment"
            },
            {
                "category": "Non-Medical Expense",
                "title": "Non-Medical Consumables"
            },
            {
                "category": "Financial Condition",
                "title": "Room Rent Limit & Proportionate Deduction"
            }
        ]
    },
    {
        "insurer": "ICICI Lombard",
        "product_name": "Health Elite (Complete Health Insurance)",
        "clauses": [
            {
                "title": "Pre-Existing Disease Waiting Period",
                "clause_type": "Waiting Period",
                "description": "Expenses related to treatment of pre-existing diseases and their direct complications are excluded until 24 months of continuous coverage.",
                "waiting_period": "24 months"
            },
            {
                "title": "30-Day Initial Waiting Period",
                "clause_type": "Waiting Period",
                "waiting_period": "30 days"
            },
            {
                "title": "Specified Disease Waiting Period",
                "clause_type": "Waiting Period",
                "waiting_period": "24 months"
            },
            {
                "title": "Investigation & Evaluation Only",
                "clause_type": "Permanent Exclusion"
            },
            {
                "title": "Cosmetic or Plastic Surgery",
                "clause_type": "Permanent Exclusion"
            },
            {
                "title": "Non-Payable Items (IRDAI List)",
                "clause_type": "Non-Payable Items"
            }
        ]
    },
    {
        "insurer": "Care Health Insurance",
        "policy_name": "Care",
        "clauses": [
            {
                "title": "Pre-Existing Disease Waiting Period",
                "category": "Pre-existing Condition",
                "waiting_period_months": 36
            },
            {
                "title": "Specific Disease Waiting Period",
                "category": "Specific Condition Waiting Period",
                "waiting_period_months": 24
            },
            {
                "title": "Initial 30-Day Waiting Period",
                "category": "Initial Waiting Period",
                "waiting_period_days": 30
            },
            {
                "title": "Medical Necessity & Reasonable Charges",
                "category": "Medical Necessity"
            },
            {
                "title": "Investigation-Only Admission",
                "category": "Diagnostic-Only Hospitalization"
            }
        ]
    },
    {
        "insurer": "Reliance General Insurance",
        "policy_name": "Health Gain",
        "clauses": [
            {
                "title": "Initial 30-Day Waiting Period",
                "category": "Initial Waiting Period",
                "waiting_period_days": 30
            },
            {
                "title": "Pre-Existing Disease Waiting Period",
                "category": "Pre-existing Condition",
                "waiting_period_months": 48
            },
            {
                "title": "Specific Disease Waiting Period",
                "category": "Specific Condition Waiting Period",
                "waiting_period_months": 24
            },
            {
                "title": "Investigation / Evaluation Only Admission",
                "category": "Diagnostic-Only Hospitalization"
            },
            {
                "title": "Medical Necessity & Reasonable Charges",
                "category": "Medical Necessity"
            },
            {
                "title": "Cosmetic / Aesthetic Treatment Exclusion",
                "category": "Permanent Exclusion"
            },
            {
                "title": "Non-Payable Items",
                "category": "Non-Medical Expense"
            }
        ]
    }
]

def get_known_providers():
    return [p.get("insurer") for p in _RAW_PROVIDER_DATA]

def get_pre_extracted_clause_risk(provider_name: str) -> dict:
    """
    Given a known provider name, convert their raw clauses into the
    10-field ClauseRiskAssessment schema.
    """
    provider = next((p for p in _RAW_PROVIDER_DATA if p.get("insurer") == provider_name), None)
    if not provider:
        return None
    
    # Default everything to 'Low Risk' or 'Moderate Risk' and adjust based on clauses
    risk_assessment = {
        "waiting_period": "Low Risk",
        "pre_existing_disease": "Low Risk",
        "room_rent_sublimit": "Low Risk",
        "disease_specific_caps": "Low Risk",
        "co_payment": "Low Risk",
        "exclusions_clarity": "Moderate Risk",
        "claim_procedure_complexity": "Low Risk",
        "sublimits_and_caps": "Low Risk",
        "restoration_benefit": "Not Found",
        "transparency_of_terms": "Low Risk",
    }
    
    raw_clauses = provider.get("clauses", [])
    
    for c in raw_clauses:
        title = c.get("title", "").lower()
        cat = c.get("category", "").lower()
        desc = c.get("description", "").lower()
        
        # Pre-existing
        if "pre-existing" in title or "ped" in title:
            months = c.get("waiting_period_months", 0)
            if "48 month" in desc or months == 48:
                risk_assessment["pre_existing_disease"] = "High Risk"
            elif "36 month" in desc or months == 36:
                risk_assessment["pre_existing_disease"] = "High Risk"
            elif "24 month" in desc or months == 24:
                risk_assessment["pre_existing_disease"] = "Moderate Risk"
                
        # Waiting period
        if "waiting" in title and "specific" not in title and "pre-existing" not in title:
            days = c.get("waiting_period_days", 0)
            if days >= 30:
                risk_assessment["waiting_period"] = "Moderate Risk"
                
        # Room rent
        if "room rent" in title or "room rent" in cat:
            risk_assessment["room_rent_sublimit"] = "Moderate Risk"
            
        # Non-payable / exclusions
        if "non-payable" in title or "non-medical" in cat or "consumables" in title:
            risk_assessment["exclusions_clarity"] = "High Risk"
            
        # Specific disease waiting (often 24 months)
        if "specific disease" in title or "specific condition" in cat:
            risk_assessment["disease_specific_caps"] = "Moderate Risk"
            
        # Co-pay
        if "co-pay" in title or "co-payment" in cat:
            risk_assessment["co_payment"] = "High Risk"

    return risk_assessment

def get_pre_extracted_summary(provider_name: str) -> str:
    provider = next((p for p in _RAW_PROVIDER_DATA if p.get("insurer") == provider_name), None)
    if not provider:
        return "Unknown Provider"
    
    return f"Pre-extracted analysis for {provider.get('insurer')} - {provider.get('policy_name', 'Health Plan')}. No AI generation was required."
