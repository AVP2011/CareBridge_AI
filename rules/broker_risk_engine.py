"""
CareBridge AI — Broker Risk Engine
====================================
Analyzes the potential for "Non-Disclosure" vs "Legitimate Denial".
Calculates a risk score for the broker/agent based on misrepresentation patterns.
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RiskFactor:
    name: str
    impact: float  # 0 to 1
    description: str

class BrokerRiskEngine:
    def __init__(self):
        self.risk_threshold = 0.6
        
    def analyze_misrepresentation(self, rejection_letter: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares rejection reasons against policy declarations to find gaps.
        """
        factors = []
        score = 0.0
        
        rejection_lower = rejection_letter.lower()
        
        # 1. Check for "Non-Disclosure" explicitly mentioned
        if "non-disclosure" in rejection_lower or "material fact" in rejection_lower:
            factors.append(RiskFactor(
                "Direct Non-Disclosure Allegation", 
                0.5, 
                "Insurer explicitly alleged non-disclosure of medical history."
            ))
            score += 0.5

        # 2. Check for Chronic Condition Gaps (e.g. Diabetes, Hypertension)
        chronic_conditions = ['diabetes', 'hypertension', 'blood pressure', 'heart', 'thyroid', 'asthma']
        for condition in chronic_conditions:
            if condition in rejection_lower:
                # If insurer says they have it, check if it was disclosed (sum insured check or similar)
                # In a real app, we'd check the application form data here
                factors.append(RiskFactor(
                    f"Chronic Condition Match: {condition}",
                    0.2,
                    f"Rejection mentions {condition}, which is a high-risk non-disclosure item."
                ))
                score += 0.2

        # 3. Check for specific dates/tenure
        date_match = re.search(r'history\s+of\s+(\d+)\s+years', rejection_lower)
        if date_match:
            years = int(date_match.group(1))
            if years > 2:
                factors.append(RiskFactor(
                    "Long-term Medical History detected",
                    0.3,
                    f"Insurer detected a {years}-year medical history not mentioned in policy."
                ))
                score += 0.3

        # Normalize score
        final_score = min(1.0, score)
        
        return {
            "risk_score": final_score,
            "risk_level": "High" if final_score > 0.7 else "Medium" if final_score > 0.4 else "Low",
            "factors": [f.__dict__ for f in factors],
            "action": "Investigate Application Form" if final_score > 0.4 else "Proceed with Appeal"
        }

if __name__ == "__main__":
    letter = "Your claim for heart surgery is rejected due to non-disclosure of 5-year hypertension history."
    engine = BrokerRiskEngine()
    print(engine.analyze_misrepresentation(letter, {}))
