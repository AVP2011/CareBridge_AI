"""
CareBridge AI - LLM Clause Extractor (Fallback)
Uses Gemma-2 2B when regex patterns fail
"""

import json
from typing import Dict, List, Optional


class LLMClauseExtractor:
    """
    Extract clauses using LLM when regex fails
    """
    
    def __init__(self, model_name="google/gemma-2-2b-it"):
        self.model_name = model_name
        # Load your model here
        # self.model = load_model(model_name)
    
    def extract_missing_clauses(
        self, 
        policy_text: str, 
        missing_clause_types: List[str]
    ) -> Dict:
        """
        Extract specific clauses using LLM
        
        Args:
            policy_text: Full policy document text
            missing_clause_types: List of clause types to extract
        
        Returns:
            Dictionary of extracted clauses
        """
        prompt = self._build_extraction_prompt(policy_text, missing_clause_types)
        
        # Call your LLM (Gemma-2 2B)
        # response = self.model.generate(prompt)
        
        # For now, return template
        response = self._mock_llm_response()
        
        # Parse LLM response to structured format
        clauses = self._parse_llm_response(response)
        
        return clauses
    
    def _build_extraction_prompt(
        self, 
        policy_text: str, 
        missing_clause_types: List[str]
    ) -> str:
        """
        Build prompt for LLM to extract specific clauses
        """
        # Clause definitions for LLM
        clause_definitions = {
            'waiting_period': 'Number of days/months before coverage begins',
            'co_payment': 'Percentage of costs patient must pay',
            'sum_insured': 'Maximum coverage amount in rupees',
            'room_rent_limit': 'Maximum daily room rent covered',
            'pre_existing_disease': 'Waiting period for pre-existing conditions',
            'maternity_coverage': 'Coverage amount and waiting period for maternity',
            'deductible': 'Amount patient pays before insurance covers',
            'policy_term': 'Duration of policy coverage',
        }
        
        # Build clause instructions
        clause_instructions = []
        for clause_type in missing_clause_types:
            definition = clause_definitions.get(clause_type, clause_type)
            clause_instructions.append(f"- {clause_type}: {definition}")
        
        clause_list = "\n".join(clause_instructions)
        
        # Truncate policy text if too long (max 3000 chars for context)
        if len(policy_text) > 3000:
            policy_text = policy_text[:3000] + "\n... (truncated)"
        
        prompt = f"""You are an expert insurance policy analyzer. Extract the following clauses from this health insurance policy.

POLICY TEXT:
{policy_text}

EXTRACT THESE CLAUSES:
{clause_list}

INSTRUCTIONS:
1. For each clause, provide:
   - value: The actual value (e.g., "30 days", "20%", "₹5,00,000")
   - confidence: Your confidence (0.0 to 1.0)
   - raw_text: The exact sentence from the policy

2. If a clause is not found, return null for that clause

3. Return ONLY valid JSON in this exact format:
{{
    "clause_type": {{
        "value": "extracted value",
        "confidence": 0.9,
        "raw_text": "exact sentence from policy"
    }}
}}

JSON OUTPUT:
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        Parse LLM JSON response into structured format
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # If LLM didn't return valid JSON, try to extract it
            # Look for JSON block in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data
                except:
                    pass
            
            print("⚠️ LLM returned invalid JSON")
            return {}
    
    def _mock_llm_response(self) -> str:
        """
        Mock LLM response for testing (replace with actual LLM call)
        """
        return json.dumps({
            "waiting_period": {
                "value": "30 days",
                "confidence": 0.95,
                "raw_text": "Coverage begins after 30 days from policy start date"
            },
            "co_payment": {
                "value": "20%",
                "confidence": 0.9,
                "raw_text": "Insured shall bear 20% of admissible claim amount"
            }
        }, indent=2)
    
    def validate_extracted_value(self, clause_type: str, value: str) -> bool:
        """
        Validate that extracted value makes sense
        """
        validation_rules = {
            'waiting_period': lambda v: any(unit in v.lower() for unit in ['day', 'month', 'year']),
            'co_payment': lambda v: '%' in v and any(char.isdigit() for char in v),
            'sum_insured': lambda v: any(c in v for c in ['₹', 'rs', 'inr']) or v.isdigit(),
            'room_rent_limit': lambda v: any(c in v for c in ['₹', 'rs', 'inr', '%']) or v.isdigit(),
        }
        
        validator = validation_rules.get(clause_type)
        if validator:
            return validator(value)
        
        return True  # No specific validation rule


# ============================================
# COMBINED EXTRACTOR (Regex + LLM)
# ============================================

class HybridClauseExtractor:
    """
    Combines regex extraction with LLM fallback
    """
    
    def __init__(self):
        from clause_extractor_comprehensive import ComprehensiveClauseExtractor
        
        self.regex_extractor = ComprehensiveClauseExtractor()
        self.llm_extractor = LLMClauseExtractor()
    
    def extract_all_clauses(self, policy_text: str) -> Dict:
        """
        Extract clauses using regex first, then LLM for missing ones
        """
        print("Step 1: Extracting with regex patterns...")
        regex_clauses = self.regex_extractor.extract_all_clauses(policy_text)
        
        print(f"✅ Found {len(regex_clauses)} clauses with regex")
        
        # Define critical clauses that MUST be extracted
        critical_clauses = [
            'waiting_period',
            'co_payment',
            'sum_insured',
            'pre_existing_disease',
            'room_rent_limit'
        ]
        
        # Find missing critical clauses
        missing = [c for c in critical_clauses if c not in regex_clauses]
        
        if missing:
            print(f"\nStep 2: Using LLM to find {len(missing)} missing clauses...")
            print(f"Missing: {', '.join(missing)}")
            
            llm_clauses = self.llm_extractor.extract_missing_clauses(
                policy_text, 
                missing
            )
            
            # Merge LLM results
            for clause_type, clause_data in llm_clauses.items():
                if clause_data and clause_type not in regex_clauses:
                    from clause_extractor_comprehensive import ExtractedClause
                    
                    regex_clauses[clause_type] = ExtractedClause(
                        clause_type=clause_type,
                        value=clause_data['value'],
                        confidence=clause_data['confidence'],
                        raw_text=clause_data['raw_text'],
                        source='llm'
                    )
                    
                    print(f"✅ LLM found: {clause_type} = {clause_data['value']}")
        else:
            print("\n✅ All critical clauses found with regex!")
        
        return regex_clauses


# ============================================
# USAGE EXAMPLE
# ============================================

def test_hybrid_extraction():
    """
    Test hybrid extractor with sample policy
    """
    sample_policy = """
    ABC Health Insurance Policy
    
    This policy provides comprehensive health coverage with the following terms:
    
    Coverage begins thirty days after policy issuance. For any pre-existing 
    medical conditions, coverage will commence after continuous coverage of 
    forty-eight months.
    
    The insured shall be responsible for twenty percent of all eligible claim 
    amounts. This cost-sharing arrangement helps keep premiums affordable.
    
    Maximum coverage provided under this policy is Five Lakh Rupees per year.
    
    For hospitalization, private room charges are covered up to Five Thousand 
    Rupees per day, or 1% of sum insured, whichever is lower.
    """
    
    extractor = HybridClauseExtractor()
    clauses = extractor.extract_all_clauses(sample_policy)
    
    # Generate report
    report = extractor.regex_extractor.generate_extraction_report(clauses)
    print("\n" + report)
    
    return clauses


if __name__ == "__main__":
    test_hybrid_extraction()
