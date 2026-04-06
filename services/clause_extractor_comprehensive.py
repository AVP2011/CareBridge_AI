"""
CareBridge AI - Comprehensive Clause Extractor
Extracts ALL important policy clauses using regex + LLM
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class ExtractedClause:
    """Represents a single extracted clause"""
    clause_type: str
    value: Any
    confidence: float  # 0.0 to 1.0
    raw_text: str
    source: str  # 'regex' or 'llm'


class ComprehensiveClauseExtractor:
    """
    Extracts policy clauses using 40+ regex patterns + LLM fallback
    """
    
    def __init__(self):
        self.patterns = self._build_patterns()
    
    def extract_all_clauses(self, policy_text: str) -> Dict[str, ExtractedClause]:
        """
        Extract all clauses from policy text
        
        Returns:
            Dictionary of clause_type -> ExtractedClause
        """
        clauses = {}
        
        # Step 1: Extract using regex patterns (fast, accurate)
        for clause_type, patterns in self.patterns.items():
            result = self._extract_with_regex(policy_text, patterns)
            if result:
                clauses[clause_type] = ExtractedClause(
                    clause_type=clause_type,
                    value=result['value'],
                    confidence=result['confidence'],
                    raw_text=result['raw_text'],
                    source='regex'
                )
        
        return clauses
    
    def _extract_with_regex(self, text: str, patterns: List[Dict]) -> Optional[Dict]:
        """
        Try multiple regex patterns for a clause type
        """
        for pattern_config in patterns:
            pattern = pattern_config['pattern']
            extractor = pattern_config.get('extractor')
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extract value using custom extractor or default
                if extractor:
                    value = extractor(match)
                else:
                    value = match.group(1) if match.groups() else match.group(0)
                
                if value:
                    return {
                        'value': value,
                        'confidence': pattern_config.get('confidence', 0.9),
                        'raw_text': match.group(0)
                    }
        
        return None
    
    def _build_patterns(self) -> Dict[str, List[Dict]]:
        """
        Build comprehensive regex patterns for all clause types
        """
        return {
            # ============================================
            # 1. WAITING PERIOD
            # ============================================
            'waiting_period': [
                {
                    'pattern': r'waiting\s+period[:\s]+(\d+)\s*(days?|months?|years?)',
                    'confidence': 0.95,
                    'extractor': lambda m: f"{m.group(1)} {m.group(2)}"
                },
                {
                    'pattern': r'(?:initial|standard)\s+waiting\s+(?:period\s+)?of\s+(\d+)\s*(days?|months?|years?)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'(\d+)\s*(days?|months?|years?)\s+waiting\s+period',
                    'confidence': 0.9
                },
                {
                    'pattern': r'covered\s+after\s+(\d+)\s*(days?|months?|years?)',
                    'confidence': 0.85
                },
                {
                    'pattern': r'shall\s+be\s+applicable\s+after\s+(\d+)\s*(days?|months?|years?)',
                    'confidence': 0.8
                },
            ],
            
            # ============================================
            # 2. CO-PAYMENT / CO-PAY
            # ============================================
            'co_payment': [
                {
                    'pattern': r'co-?pay(?:ment)?[:\s]+(\d+)%',
                    'confidence': 0.95,
                    'extractor': lambda m: f"{m.group(1)}%"
                },
                {
                    'pattern': r'(?:insured|policyholder|patient)\s+(?:shall|will|must)\s+(?:pay|bear)\s+(\d+)%',
                    'confidence': 0.9
                },
                {
                    'pattern': r'(\d+)%\s+(?:of|payable by)\s+(?:insured|policyholder|patient)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'deductible[:\s]+(\d+)%',
                    'confidence': 0.85
                },
                {
                    'pattern': r'cost\s+sharing[:\s]+(\d+)%',
                    'confidence': 0.8
                },
            ],
            
            # ============================================
            # 3. SUM INSURED
            # ============================================
            'sum_insured': [
                {
                    'pattern': r'sum\s+insured[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.95,
                    'extractor': lambda m: f"₹{m.group(1).replace(',', '')}"
                },
                {
                    'pattern': r'coverage\s+(?:amount|limit)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'insured\s+for\s+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.85
                },
                {
                    'pattern': r'maximum\s+(?:coverage|limit)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.85
                },
            ],
            
            # ============================================
            # 4. ROOM RENT LIMIT
            # ============================================
            'room_rent_limit': [
                {
                    'pattern': r'room\s+rent\s+limit[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'room\s+charges?[:\s]+(?:upto|up\s+to|maximum)\s+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'(?:single|private)\s+room[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)\s+per\s+day',
                    'confidence': 0.9
                },
                {
                    'pattern': r'(\d+)%\s+of\s+sum\s+insured\s+for\s+room\s+rent',
                    'confidence': 0.85,
                    'extractor': lambda m: f"{m.group(1)}% of SI"
                },
            ],
            
            # ============================================
            # 5. PRE-EXISTING DISEASE
            # ============================================
            'pre_existing_disease': [
                {
                    'pattern': r'pre-?existing\s+disease[s]?[:\s]+covered\s+after\s+(\d+)\s*(months?|years?)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'PED\s+(?:waiting\s+period|coverage)[:\s]+(\d+)\s*(months?|years?)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'diseases?\s+existing\s+prior\s+to\s+policy[:\s]+(\d+)\s*(months?|years?)',
                    'confidence': 0.85
                },
                {
                    'pattern': r'pre-?existing\s+(?:conditions?|diseases?)\s+(?:excluded|not\s+covered)\s+for\s+(\d+)\s*(months?|years?)',
                    'confidence': 0.9
                },
            ],
            
            # ============================================
            # 6. MATERNITY COVERAGE
            # ============================================
            'maternity_coverage': [
                {
                    'pattern': r'maternity\s+(?:benefit|coverage)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'normal\s+delivery[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.9
                },
                {
                    'pattern': r'maternity\s+waiting\s+period[:\s]+(\d+)\s*(months?|years?)',
                    'confidence': 0.9,
                    'extractor': lambda m: f"Waiting: {m.group(1)} {m.group(2)}"
                },
            ],
            
            # ============================================
            # 7. CLAIM SETTLEMENT
            # ============================================
            'claim_settlement_ratio': [
                {
                    'pattern': r'claim\s+settlement\s+ratio[:\s]+(\d+(?:\.\d+)?)%',
                    'confidence': 0.95
                },
                {
                    'pattern': r'CSR[:\s]+(\d+(?:\.\d+)?)%',
                    'confidence': 0.9
                },
            ],
            
            # ============================================
            # 8. PREMIUM
            # ============================================
            'premium_amount': [
                {
                    'pattern': r'(?:annual|yearly)\s+premium[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'premium\s+(?:payable|amount)[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.9
                },
            ],
            
            # ============================================
            # 9. POLICY TERM
            # ============================================
            'policy_term': [
                {
                    'pattern': r'policy\s+(?:term|period|tenure)[:\s]+(\d+)\s*(years?|months?)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'coverage\s+(?:for|period)[:\s]+(\d+)\s*(years?|months?)',
                    'confidence': 0.9
                },
            ],
            
            # ============================================
            # 10. RENEWAL
            # ============================================
            'renewal_age': [
                {
                    'pattern': r'renewable\s+(?:upto|up\s+to|till)\s+(?:age\s+)?(\d+)\s*years?',
                    'confidence': 0.95
                },
                {
                    'pattern': r'lifelong\s+renewability',
                    'confidence': 0.95,
                    'extractor': lambda m: "Lifelong"
                },
            ],
            
            # ============================================
            # 11. CASHLESS NETWORK
            # ============================================
            'cashless_hospitals': [
                {
                    'pattern': r'(\d+[,\d]*)\s+(?:cashless\s+)?hospitals?',
                    'confidence': 0.9,
                    'extractor': lambda m: f"{m.group(1)} hospitals"
                },
                {
                    'pattern': r'network\s+of\s+(\d+[,\d]*)\s+hospitals?',
                    'confidence': 0.85
                },
            ],
            
            # ============================================
            # 12. EXCLUSIONS (Common)
            # ============================================
            'exclusions': [
                {
                    'pattern': r'(?:not\s+covered|excluded)[:\s]+(.*?)(?:\n|\.)',
                    'confidence': 0.7,
                    'extractor': lambda m: m.group(1).strip()
                },
            ],
            
            # ============================================
            # 13. DEDUCTIBLE
            # ============================================
            'deductible': [
                {
                    'pattern': r'deductible[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.95
                },
                {
                    'pattern': r'excess[:\s]+(?:Rs\.?|INR|₹)?\s*([\d,]+)',
                    'confidence': 0.9
                },
            ],
            
            # ============================================
            # 14. SUB-LIMITS
            # ============================================
            'sub_limits': [
                {
                    'pattern': r'sub-?limit[:\s]+(.*?)(?:\n|\.)',
                    'confidence': 0.8
                },
                {
                    'pattern': r'capping[:\s]+(.*?)(?:\n|\.)',
                    'confidence': 0.75
                },
            ],
            
            # ============================================
            # 15. NO CLAIM BONUS
            # ============================================
            'no_claim_bonus': [
                {
                    'pattern': r'no\s+claim\s+bonus[:\s]+(\d+)%',
                    'confidence': 0.95
                },
                {
                    'pattern': r'NCB[:\s]+(\d+)%',
                    'confidence': 0.9
                },
                {
                    'pattern': r'bonus\s+of\s+(\d+)%\s+(?:for|on)\s+no\s+claim',
                    'confidence': 0.85
                },
            ],
        }
    
    def extract_with_llm(self, policy_text: str, missing_clauses: List[str]) -> Dict[str, ExtractedClause]:
        """
        Use LLM to extract clauses that regex missed
        
        TODO: Implement this with your MedGemma model
        """
        # This will be called if regex misses important clauses
        pass
    
    def generate_extraction_report(self, clauses: Dict[str, ExtractedClause]) -> str:
        """
        Generate human-readable report of extracted clauses
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("POLICY CLAUSE EXTRACTION REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # Group by category
        critical_clauses = ['waiting_period', 'co_payment', 'sum_insured', 'pre_existing_disease']
        financial_clauses = ['premium_amount', 'deductible', 'room_rent_limit']
        benefit_clauses = ['maternity_coverage', 'no_claim_bonus', 'cashless_hospitals']
        
        def print_section(title, clause_types):
            found_any = False
            for clause_type in clause_types:
                if clause_type in clauses:
                    if not found_any:
                        report_lines.append(f"\n{title}:")
                        report_lines.append("-" * 40)
                        found_any = True
                    
                    clause = clauses[clause_type]
                    label = clause_type.replace('_', ' ').title()
                    confidence_emoji = "✅" if clause.confidence >= 0.9 else "⚠️"
                    
                    report_lines.append(f"{confidence_emoji} {label}: {clause.value}")
                    report_lines.append(f"   Source: {clause.raw_text[:80]}...")
                    report_lines.append("")
        
        print_section("CRITICAL CLAUSES", critical_clauses)
        print_section("FINANCIAL TERMS", financial_clauses)
        print_section("BENEFITS & FEATURES", benefit_clauses)
        
        # Summary
        report_lines.append("\n" + "=" * 60)
        report_lines.append(f"TOTAL CLAUSES FOUND: {len(clauses)}")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)


# ============================================
# USAGE EXAMPLE
# ============================================

def test_clause_extraction():
    """
    Test the clause extractor with sample policy text
    """
    # Sample policy text (replace with your actual PDF text)
    sample_policy = """
    HEALTH INSURANCE POLICY
    
    Sum Insured: Rs. 5,00,000
    Annual Premium: Rs. 12,500
    
    COVERAGE DETAILS:
    1. Waiting Period: 30 days for all illnesses
    2. Pre-existing diseases covered after 48 months
    3. Co-payment: 20% applicable for insured aged 60+
    4. Room Rent Limit: Rs. 5,000 per day
    5. Maternity Benefit: Rs. 50,000 after 36 months waiting period
    
    NETWORK:
    Cashless treatment available at 10,000+ hospitals
    
    BONUS:
    No Claim Bonus: 10% increase in sum insured each claim-free year
    
    EXCLUSIONS:
    Not covered: Cosmetic surgery, dental treatment, eyeglasses
    """
    
    extractor = ComprehensiveClauseExtractor()
    
    # Extract clauses
    clauses = extractor.extract_all_clauses(sample_policy)
    
    # Generate report
    report = extractor.generate_extraction_report(clauses)
    print(report)
    
    # Export to JSON
    clauses_json = {
        k: {
            'value': v.value,
            'confidence': v.confidence,
            'raw_text': v.raw_text,
            'source': v.source
        }
        for k, v in clauses.items()
    }
    
    with open("extracted_clauses.json", "w") as f:
        json.dump(clauses_json, f, indent=2)
    
    print("\n✅ Clauses saved to: extracted_clauses.json")
    
    return clauses


if __name__ == "__main__":
    test_clause_extraction()
