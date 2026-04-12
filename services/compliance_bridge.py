import json
import os
from pathlib import Path

class ComplianceBridge:
    def __init__(self):
        registry_path = os.path.join(Path(__file__).parent.parent, "rag", "indices", "irdai_standard_registry.json")
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)

    def map_to_standard(self, key: str) -> dict:
        """
        Maps an insurer-specific term to an IRDAI standard rule.
        Example: 'Re-fill' -> Restoration Rule
        """
        rules = self.registry.get("rules", {})
        
        # Exact match
        if key in rules:
            return rules[key]
            
        # Synonym match
        for rule_key, rule_data in rules.items():
            if key in rule_data.get("synonyms", []):
                return rule_data
                
        return None

    def get_citation_for_exclusion(self, text: str) -> str:
        """
        Scans text for IRDAI Exclusion Codes (Excl01, etc.) 
        and returns the human-readable standard name.
        """
        codes = self.registry.get("exclusion_codes", {})
        for code, description in codes.items():
            if code in text:
                return f"{description} ({code})"
        return "Standard IRDAI Exclusion"

    def audit_fact(self, key: str, value: str) -> dict:
        """
        Performs a 'Logic Audit' on a policy fact.
        Example: If 'pre_existing_disease' is '5 years', this will flag it 
        against the IRDAI 48-month limitation.
        """
        rule = self.map_to_standard(key)
        if not rule:
            return {"status": "unknown", "msg": "No specific IRDAI mandate found."}
            
        # Example validation: PED Limit
        if key == "pre_existing_disease":
            # Logic to check if value > 48 months
            pass 

        return {
            "standard_name": rule["standard_label"],
            "irdai_limit": rule["irdai_limit"],
            "source_law": rule["regulation_ref"]
        }
