# services/clause_matcher.py

import re
from typing import Dict, List, Optional, Any
from services.synonyms import get_synonyms

class ClauseMatcher:
    """
    Normalizes and validates extracted policy clauses.
    Ensures that values match industry formats and handles synonyms.
    """

    def __init__(self):
        # Map of clause types to their expected standard formats
        self.standard_formats = {
            "waiting_period": r"(\d+)\s*(days?|months?|years?)",
            "co_payment": r"(\d+)%",
            "sum_insured": r"₹?([\d,]+)",
            "room_rent_limit": r"(?:₹?([\d,]+)|(?:single|private)\s*room|no\s*limit)",
        }

    def normalize_value(self, clause_type: str, raw_value: str) -> Any:
        """
        Normalize a raw value into a standard format
        """
        if not raw_value:
            return "Not Found"
            
        val_lower = str(raw_value).lower().strip()
        
        # Specific normalization logic
        if clause_type == "waiting_period":
            match = re.search(self.standard_formats[clause_type], val_lower)
            if match:
                return f"{match.group(1)} {match.group(2)}"
        
        if clause_type == "co_payment":
            match = re.search(self.standard_formats[clause_type], val_lower)
            if match:
                return f"{match.group(1)}%"
                
        if clause_type == "sum_insured":
            # Remove currency symbols and commas
            nums = re.findall(r'\d+', val_lower.replace(',', ''))
            if nums:
                return f"₹{int(nums[0]):,}"

        return raw_value.capitalize()

    def get_risk_level(self, clause_type: str, value: Any) -> str:
        """
        Basic risk scoring based on policy values
        """
        val_str = str(value).lower()
        
        if clause_type == "co_payment":
            digits = re.findall(r'\d+', val_str)
            if digits and int(digits[0]) > 20:
                return "HIGH"
            if digits and int(digits[0]) > 0:
                return "MODERATE"
            return "LOW"
            
        if clause_type == "waiting_period":
            if "year" in val_str or ("month" in val_str and int(re.findall(r'\d+', val_str)[0]) > 12):
                return "MODERATE"
                
        return "LOW"

    def match_with_standards(self, extracted_clauses: Dict) -> Dict:
        """
        Enhances extraction with standard comparison flags
        """
        for c_type, clause in extracted_clauses.items():
            clause.normalized_value = self.normalize_value(c_type, clause.value)
            clause.risk_level = self.get_risk_level(c_type, clause.normalized_value)
            
        return extracted_clauses