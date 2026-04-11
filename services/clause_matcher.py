import json
import re
from typing import Dict, List, Optional, Any

from schemas.intermediate import ClauseMatchResult
from llm.generation import generate
from llm.prompts import clause_matching_prompt


_CLAUSE_DEFAULTS = {
    "clause_category":     "Other / unclear",
    "clause_detected":     "Not found in policy text",
    "clause_clarity":      "Low",
    "rejection_alignment": "Partial",
    "explanation":         "Unable to confidently identify a matching policy clause.",
    "confidence":          "Low",
}


def _safe_json_parse(raw: str) -> dict | None:
    """Try clean parse, then outermost-block extraction."""
    if not raw: return None
    try:
        return json.loads(raw.strip())
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


def run_clause_matcher(
    model,
    tokenizer,
    policy_text:      str,
    rejection_text:   str,
    user_context:     str | None = None,
) -> ClauseMatchResult:
    """
    LLM-based clause category matching for Indian health insurance.
    """
    # 🔒 Strict input truncation to prevent prompt overflow
    policy_text    = re.sub(r"\s+", " ", (policy_text    or "").strip())[:3000]
    rejection_text = re.sub(r"\s+", " ", (rejection_text or "").strip())[:1000]
    user_context   = re.sub(r"\s+", " ", (user_context   or "").strip())[:500]

    prompt = clause_matching_prompt(policy_text, rejection_text, user_context)

    # Two attempts with JSON validation
    for attempt in range(2):
        raw_output = generate(
            prompt, model, tokenizer,
            json_mode=True,
            max_new_tokens=256,
        )

        print(f"RAW CLAUSE OUTPUT (attempt {attempt + 1}):", raw_output)

        parsed = _safe_json_parse(raw_output)
        if parsed is None:
            continue

        # Sync key names (LLM might use underscores or camelCase, though prompt is specific)
        for key, default in _CLAUSE_DEFAULTS.items():
            parsed.setdefault(key, default)

        try:
            return ClauseMatchResult(**parsed)
        except Exception as e:
            print(f"⚠️ ClauseMatchResult validation failed (attempt {attempt + 1}):", e)
            continue

    print("⚠️ Clause matching fallback triggered")
    return ClauseMatchResult(**_CLAUSE_DEFAULTS)


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