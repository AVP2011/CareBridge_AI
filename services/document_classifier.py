import re
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel

class ClassificationResult(BaseModel):
    document_type: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = {}

class DocumentClassifier:
    """
    Classifies documents based on health insurance domain logic.
    """
    
    CLASSES = {
        "HEALTH_POLICY": {
            "keywords": [r"policy schedule", r"sum insured", r"waiting period", r"standard exclusion", r"irdai registration", r"certificate of insurance", r"policy number", r"contract of insurance"],
            "weight": 2.5
        },
        "INSURANCE_BROCHURE": {
            "keywords": [r"marketing", r"brochure", r"why buy", r"product highlight", r"illustrative", r"brochure code"],
            "weight": 1.5
        },
        "CLAIM_REJECTION": {
            "keywords": [r"repudiation", r"rejection letter", r"claim not admitted", r"not payable", r"claim reference"],
            "weight": 2.0
        },
        "MEDICAL_RECORD": {
            "keywords": [r"chief complaints", r"medical history", r"diagnosis", r"on examination", r"procedure", r"discharge summary"],
            "weight": 1.8
        },
        "HOSPITAL_BILL": {
            "keywords": [r"total amount", r"invoice", r"final bill", r"payable", r"breakup", r"summary of charges"],
            "weight": 1.8
        }
    }

    def classify(self, text: str) -> ClassificationResult:
        if not text:
            return ClassificationResult(document_type="UNKNOWN", confidence=0.0, reasoning="Empty document.")

        text_lower = text.lower()
        scores = {cls: 0.0 for cls in self.CLASSES}
        
        for cls, cfg in self.CLASSES.items():
            matches = 0
            for kw in cfg["keywords"]:
                if re.search(kw, text_lower):
                    matches += 1
            
            # Normalise matches by keyword count and apply weight
            scores[cls] = (matches / len(cfg["keywords"])) * cfg["weight"]

        # Find best match
        best_cls = max(scores, key=scores.get)
        max_score = scores[best_cls]

        # Calculate confidence (rough heuristic)
        # 1.0 = highly confident, >0.5 = confident
        confidence = min(max_score / 1.5, 1.0) 

        if max_score < 0.2:
            return ClassificationResult(
                document_type="NON_INSURANCE",
                confidence=0.9,
                reasoning="No domain-specific patterns found. Possibly a generic document."
            )

        # Refine reasoning
        reasoning = f"Detected patterns for {best_cls} (matches: {int(max_score * 5)})."
        
        return ClassificationResult(
            document_type=best_cls,
            confidence=round(confidence, 2),
            reasoning=reasoning
        )

if __name__ == "__main__":
    classifier = DocumentClassifier()
    print(classifier.classify("This is a policy schedule with sum insured of 500000."))
    print(classifier.classify("Patient presents with fever and cough. Discharge summary details."))
    print(classifier.classify("Total amount payable for the final bill is 150000."))
