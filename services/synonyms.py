# services/synonyms.py

CLAUSE_SYNONYMS = {
    "waiting_period": [
        "waiting period", "exclusion period", "cooling off", "initial waiting", 
        "standard waiting", "time-bound restriction", "not covered for 30 days",
        "exclusion for first", "waiting for 30 days"
    ],
    "pre_existing_disease": [
        "pre-existing", "pre existing", "preexisting", "ped", "known illness",
        "pre-existing conditions", "declared illnesses", "history of illness"
    ],
    "co_payment": [
        "co-pay", "copay", "co payment", "co-payment", "cost sharing",
        "deductible", "member's share", "insured's contribution", "pay 20%"
    ],
    "room_rent_limit": [
        "room rent", "room charges", "room limit", "room rent cap",
        "single private room", "room rent sublimit", "room rent percentage"
    ],
    "restoration_benefit": [
        "restoration", "sum insured restoration", "refill", "reinstatement",
        "automatic restoration", "restore sum insured"
    ],
    "maternity_coverage": [
        "maternity", "delivery", "pregnancy", "childbirth", "newborn",
        "maternity expenses", "delivery charges"
    ],
    "disease_caps": [
        "sub-limit", "sublimit", "disease cap", "capping", "maximum payout",
        "limit per disease", "specific illness limit"
    ]
}

def get_synonyms(clause_type):
    return CLAUSE_SYNONYMS.get(clause_type, [])
