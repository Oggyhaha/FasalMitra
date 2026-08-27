import re
from typing import Dict, List, Any

class QueryUnderstandingEngine:
    def __init__(self):
        self.crop_dictionary = {
            "soybean": ["soybean", "सोयाबीन", "सोयाबिन"],
            "cotton": ["cotton", "कापूस", "कपास"],
            "wheat": ["wheat", "गहू", "गेहूं"],
            "gram": ["gram", "चना", "हरभरा", "chickpea"],
            "rice": ["rice", "भात", "धान", "चावल"],
            "sugarcane": ["sugarcane", "ऊस", "गन्ना"]
        }
        
        self.symptom_dictionary = {
            "yellowing": ["yellowing", "yellow", "पिवळी", "पिवळा", "पीले", "पीला"],
            "bollworm": ["bollworm", "अळी", "इल्ली", "अल्ली"],
            "rust": ["rust", "तांबेरा", "गेरुआ"],
            "wilt": ["wilt", "उबाळणी", "सूखना"],
            "yield_planning": ["yield", "crop selection", "उत्पन्न", "उत्पादन", "फसल चयन", "लागवड", "बोएं"]
        }
        
        self.chemical_dictionary = [
            "chlorpyrifos", "thiamethoxam", "monocrotophos", "imidacloprid", "paraquat", "glyphosate"
        ]

    def parse_query(self, text: str, crop_override: str = None) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Crop identification
        detected_crop = crop_override
        if not detected_crop:
            for canonical, synonyms in self.crop_dictionary.items():
                if any(syn in text_lower for syn in synonyms):
                    detected_crop = canonical.capitalize()
                    break
        if not detected_crop:
            detected_crop = "General"

        # Symptom / Intent extraction
        detected_symptoms = []
        for canonical, synonyms in self.symptom_dictionary.items():
            if any(syn in text_lower for syn in synonyms):
                detected_symptoms.append(canonical)

        # Chemical extraction
        detected_chemicals = []
        for chem in self.chemical_dictionary:
            if chem in text_lower:
                detected_chemicals.append(chem)

        # Intent classification
        intent = "GENERAL_CROP"
        if any(kw in text_lower for kw in ["yield", "which crop", "crop to sow", "काय पिक घ्यावे", "कौन सी फसल"]):
            intent = "CROP_SELECTION"
        elif detected_symptoms or "कीड" in text_lower or "कीड़ा" in text_lower:
            intent = "PEST_DISEASE"
        elif any(kw in text_lower for kw in ["फवारणी", "स्प्रे", "मात्रा", "dose"]):
            intent = "INPUT_USAGE"
        elif any(kw in text_lower for kw in ["पाणी", "सिंचाई", "irrigation"]):
            intent = "IRRIGATION"
        elif any(kw in text_lower for kw in ["पेरणी", "बुआई", "sowing"]):
            intent = "SOWING"
        elif any(kw in text_lower for kw in ["मौसम", "हवामान", "rain", "पाऊस"]):
            intent = "WEATHER"

        urgency = "HIGH" if len(detected_symptoms) > 1 or detected_chemicals else "MEDIUM"

        return {
            "intent": intent,
            "crop": detected_crop,
            "symptoms": detected_symptoms,
            "chemicals_mentioned": detected_chemicals,
            "urgency": urgency
        }

query_understanding_engine = QueryUnderstandingEngine()
