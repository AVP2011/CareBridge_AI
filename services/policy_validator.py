import re
from typing import Tuple

# Keywords that should be present in a health insurance policy document
MANDATORY_KEYWORDS = [
    r"sum insured",
    r"policy",
    r"insurer",
    r"insured",
    r"claim",
    r"benefit",
    r"exclusion",
    r"waiting period",
]

# Keywords that strongly suggest it's a health insurance policy
STRONG_KEYWORDS = [
    r"pre-existing disease",
    r"co-payment",
    r"domiciliary",
    r"in-patient",
    r"hospitalization",
    r"day care treatment",
    r"ayush",
    r"irdai",
    r"restoration benefit",
    r"room rent",
]

def is_health_insurance_policy(text: str) -> Tuple[bool, str]:
    """
    Analyzes the text to determine if it's a health insurance policy document.
    Returns (is_policy, reason).
    """
    if not text or len(text.strip()) < 200:
        return False, "Document is too short to be a valid health insurance policy."

    text_lower = text.lower()
    
    # 1. Check for mandatory insurance keywords
    mandatory_count = sum(1 for k in MANDATORY_KEYWORDS if re.search(k, text_lower))
    
    # 2. Check for strong health insurance specific keywords
    strong_count = sum(1 for k in STRONG_KEYWORDS if re.search(k, text_lower))
    
    # Logic for validation
    # If we have at least 4 mandatory and 2 strong keywords, we consider it a policy.
    # Adjusting for OCR quality: sometimes text is garbled, so we use lower thresholds if needed.
    
    if mandatory_count >= 3 and strong_count >= 2:
        return True, "Valid health insurance policy detected."
    
    if mandatory_count >= 5:
        return True, "General insurance document detected (likely health)."

    # 3. Last fallback: Check for very specific phrases
    if "irdai" in text_lower and "health insurance" in text_lower:
        return True, "Official IRDAI health insurance document detected."

    return False, "This document does not look like a health insurance policy. Please upload a valid Policy Wording or Schedule."

if __name__ == "__main__":
    # Small test
    test_text = "This is a health insurance policy with sum insured of 5 lakhs. It covers hospitalization and has a waiting period of 2 years for pre-existing diseases."
    print(is_health_insurance_policy(test_text))
    
    fake_text = "This is a recipe for a cake. You need flour, sugar, and eggs. Bake for 30 minutes at 180 degrees."
    print(is_health_insurance_policy(fake_text))
