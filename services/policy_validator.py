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

from services.document_classifier import DocumentClassifier

def is_health_insurance_policy(text: str) -> Tuple[bool, str]:
    """
    Analyzes the text using the DocumentClassifier to verify it's a health policy.
    Returns (is_policy, reason).
    """
    if not text or len(text.strip()) < 200:
        return False, "Document is too short to be a valid health insurance policy."

    classifier = DocumentClassifier()
    result = classifier.classify(text)

    if result.document_type == "HEALTH_POLICY":
        if result.confidence >= 0.5:
            return True, "Valid health insurance policy detected."
        else:
            return False, "Document looks like a policy but has low clarity (OCR issue?). Please upload a better scan."

    if result.document_type == "INSURANCE_BROCHURE":
        return False, "This looks like a Marketing Brochure. Please upload the 'Policy Wording' or 'Policy Schedule' for analysis."

    if result.document_type == "CLAIM_REJECTION":
        return False, "This looks like a Claim Rejection Letter. Please use the 'Audit Rejection' tool instead."

    if result.document_type == "MEDICAL_RECORD":
        return False, "This is a Medical Record / Discharge Summary. Analysis is only performed on Insurance Policies."

    if result.document_type == "HOSPITAL_BILL":
        return False, "This is a Hospital Bill. Analysis is only performed on Insurance Policies."

    return False, f"Document rejected: {result.reasoning} Please upload a standard Health Insurance Policy document."

if __name__ == "__main__":
    # Small test
    test_text = "This is a health insurance policy with sum insured of 5 lakhs. It covers hospitalization and has a waiting period of 2 years for pre-existing diseases."
    print(is_health_insurance_policy(test_text))
    
    fake_text = "This is a recipe for a cake. You need flour, sugar, and eggs. Bake for 30 minutes at 180 degrees."
    print(is_health_insurance_policy(fake_text))
