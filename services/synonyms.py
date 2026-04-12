# services/synonyms.py

CLAUSE_SYNONYMS = {
    "waiting_period": [
        "waiting period", "exclusion period", "cooling off", "initial waiting", 
        "standard waiting", "time-bound restriction", "not covered for 30 days",
        "exclusion for first", "waiting for 30 days", "specific disease waiting"
    ],
    "pre_existing_disease": [
        "pre-existing", "pre existing", "preexisting", "ped", "known illness",
        "pre-existing conditions", "declared illnesses", "history of illness",
        "existence of any condition before"
    ],
    "co_payment": [
        "co-pay", "copay", "co payment", "co-payment", "cost sharing",
        "deductible", "member's share", "insured's contribution", "pay 20%",
        "share of each and every claim"
    ],
    "room_rent_limit": [
        "room rent", "room charges", "room limit", "room rent cap",
        "single private room", "room rent sublimit", "room rent percentage",
        "twin sharing", "single standard ac room", "room category", "standard ward",
        "limit on cabin", "proportional deduction"
    ],
    "restoration_benefit": [
        "restoration", "sum insured restoration", "refill", "re-fill", "reinstatement",
        "automatic restoration", "restore sum insured", "reassure", "recovery booster",
        "multiplier benefit", "exhaustion of sum insured"
    ],
    "maternity_coverage": [
        "maternity", "delivery", "pregnancy", "childbirth", "newborn",
        "maternity expenses", "delivery charges", "obstetric"
    ],
    "disease_caps": [
        "sub-limit", "sublimit", "disease cap", "capping", "maximum payout",
        "limit per disease", "specific illness limit", "caps on surgery",
        "modern treatment limit"
    ],
    "no_claim_bonus": [
        "ncb", "cumulative bonus", "no claim bonus", "renewal incentive",
        "multiplier", "bonus for every claim free year"
    ]
}

def get_synonyms(clause_type):
    return CLAUSE_SYNONYMS.get(clause_type, [])
