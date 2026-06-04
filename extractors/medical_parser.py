"""
CareBridge AI — Medical Term Parser
====================================
Detects and normalizes medical conditions from rejection letters and policy documents.
Provides mapping to standard ICD-like categories for better rule matching.

Capabilities:
  - Disease entity extraction (Regex based for high reliability)
  - ICD category mapping (Pre-defined dictionary)
  - Chronic/Acute condition detection
  - Complexity scoring for MedGemma prioritization
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Dict, Optional

# ─────────────────────────────────────────────
# Medical Categories & Keywords
# ─────────────────────────────────────────────

MEDICAL_TAXONOMY = {
    "CARDIOVASCULAR": {
        "keywords": [r"hypertension", r"htn", r"cardiac", r"heart", r"myocardial", r"infarction", r"stent", r"angioplasty", r"coronary", r"bp", r"blood pressure"],
        "chronic": True,
        "icd_prefix": "I"
    },
    "ENDOCRINE": {
        "keywords": [r"diabetes", r"dm", r"t2dm", r"t1dm", r"insulin", r"thyroid", r"hyperthyroid", r"hypothyroid", r"sugar", r"glucose"],
        "chronic": True,
        "icd_prefix": "E"
    },
    "RESPIRATORY": {
        "keywords": [r"asthma", r"copd", r"bronchitis", r"pneumonia", r"respiratory", r"lung"],
        "chronic": True,
        "icd_prefix": "J"
    },
    "GASTRO": {
        "keywords": [r"gastric", r"hernia", r"appendix", r"appendicitis", r"liver", r"cirrhosis", r"gallbladder", r"stone", r"calculus"],
        "chronic": False,
        "icd_prefix": "K"
    },
    "ORTHO": {
        "keywords": [r"fracture", r"knee", r"joint", r"replacement", r"spine", r"back pain", r"disc", r"arthritis", r"osteo"],
        "chronic": True,
        "icd_prefix": "M"
    },
    "OPHTHALMIC": {
        "keywords": [r"cataract", r"glaucoma", r"retina", r"vision", r"lasik"],
        "chronic": False,
        "icd_prefix": "H"
    },
    "NEPHRO": {
        "keywords": [r"kidney", r"renal", r"dialysis", r"calculus", r"stone"],
        "chronic": True,
        "icd_prefix": "N"
    }
}

@dataclass
class MedicalEntity:
    term: str
    category: str
    is_chronic: bool
    icd_group: str
    raw_snippet: str

class MedicalParser:
    """
    Parses text for medical conditions and categorizes them.
    Used to inform the rejection engine about the 'nature' of the illness.
    """
    
    def __init__(self):
        # Pre-compile patterns
        self.patterns = {}
        for category, data in MEDICAL_TAXONOMY.items():
            combined_p = "|".join(data["keywords"])
            self.patterns[category] = re.compile(rf"\b({combined_p})\b", re.IGNORECASE)

    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extracts known medical conditions from text.
        """
        found_entities = []
        text_lower = text.lower()
        
        for category, pattern in self.patterns.items():
            matches = pattern.finditer(text_lower)
            for m in matches:
                # Capture a bit of context
                start = max(0, m.start() - 20)
                end = min(len(text), m.end() + 20)
                snippet = text[start:end].strip()
                
                entity = MedicalEntity(
                    term=m.group(0),
                    category=category,
                    is_chronic=MEDICAL_TAXONOMY[category]["chronic"],
                    icd_group=MEDICAL_TAXONOMY[category]["icd_prefix"],
                    raw_snippet=snippet
                )
                found_entities.append(entity)
                
        return self._deduplicate(found_entities)

    def _deduplicate(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        unique = {}
        for e in entities:
            key = f"{e.category}:{e.term.lower()}"
            if key not in unique:
                unique[key] = e
        return list(unique.values())

    def get_medical_context_string(self, text: str) -> str:
        """
        Returns a concise summary of the medical findings in the text.
        Useful for prompting MedGemma.
        """
        entities = self.extract_entities(text)
        if not entities:
            return "No specific medical conditions identified using regex pattern matching."
        
        summary = "Identified Medical Conditions:\n"
        for e in entities:
            chronic_str = "[Chronic]" if e.is_chronic else "[Acute/Specific]"
            summary += f"- {e.term.upper()} (Category: {e.category}, {chronic_str})\n"
        
        return summary

def get_medical_parser() -> MedicalParser:
    return MedicalParser()
