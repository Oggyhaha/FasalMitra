import re
from typing import Dict, List, Any

class QueryUnderstandingEngine:
    def __init__(self):
        self.crop_dictionary = {
            "soybean": ["soybean", "soyabean", "सोयाबीन", "सोयाबिन", "सोया", "bhat"],
            "cotton": ["cotton", "कापूस", "कपास", "kapas"],
            "wheat": ["wheat", "गहू", "गेहूं", "gehun"],
            "chickpea": ["gram", "chickpea", "चना", "हरभरा", "chana", "harbhara"],
            "rice": ["rice", "paddy", "भात", "धान", "चावल", "dhan"],
            "sugarcane": ["sugarcane", "ऊस", "गन्ना", "ganna"],
            "groundnut": ["groundnut", "peanut", "भुईमूग", "मूंगफली", "mungphalli"],
            "mustard": ["mustard", "मोहरी", "सरसों", "sarson", "raya"],
            "chilli": ["chilli", "chili", "मिरची", "मिर्च", "mirch", "mirchi"],
            "tomato": ["tomato", "टोमॅटो", "टमाटर", "tamatar"],
            "onion": ["onion", "कांदा", "प्याज", "pyaj", "kanda"],
            "potato": ["potato", "बटाटा", "आलू", "aloo", "batata"],
            "maize": ["maize", "corn", "मका", "मक्का", "makka"],
            "pigeonpea": ["pigeonpea", "arhar", "tur", "तूर", "अरहर"],
            "mango": ["mango", "आंबा", "आम", "aam"],
            "bajra": ["bajra", "pearl millet", "बाजरी", "बाजरा"]
        }
        
        self.symptom_dictionary = {
            "yellowing": ["yellowing", "yellow", "पिवळी", "पिवळा", "पीले", "पीला", "पीलापन", "chlorosis"],
            "bollworm": ["bollworm", "अळी", "इल्ली", "अल्ली", "pink bollworm", "गुलाबी इल्ली", "गुलाबी अळी", "बोंड अळी", "बोंडअळी"],
            "rust": ["rust", "तांबेरा", "गेरुआ", "yellow rust", "पीला रतुआ", "पिवळा रतुआ", "रतुआ"],
            "wilt": ["wilt", "उबाळणी", "सूखना", "मुरझाना", "मर रोग"],
            "blast": ["blast", "ब्लास्ट", "ब्लास्ट रोग", "rice blast", "भात ब्लास्ट", "धान ब्लास्ट", "blight", "करपा"],
            "shoot_borer": ["shoot borer", "बोरर", "खोडकिडा", "तना छेदक", "dead heart"],
            "whitefly": ["whitefly", "पांढरी माशी", "सफेद मक्खी"],
            "aphid": ["aphid", "मावा", "चेपा"],
            "thrips": ["thrips", "थ्रिप्स", "फुलकिडे"],
            "yield_planning": ["yield", "crop selection", "उत्पन्न", "उत्पादन", "फसल चयन", "लागवड", "बोएं", "काय पिक घ्यावे", "कोणते पीक", "कौन सी फसल"]
        }
        
        self.chemical_dictionary = [
            "chlorpyrifos", "thiamethoxam", "monocrotophos", "imidacloprid", "paraquat", "glyphosate",
            "triclopyr", "triclazole", "propiconazole", "chlorantraniliprole", "emamectin", "spinetoram",
            "fipronil", "haNPV", "npv", "carbendazim", "mancozeb"
        ]

    def parse_query(self, text: str, crop_override: str = None) -> Dict[str, Any]:
        text_lower = text.lower()
        
        # Crop identification
        # Check text first unless a valid non-General override is provided
        detected_crop = None
        for canonical, synonyms in self.crop_dictionary.items():
            if any(syn in text_lower for syn in synonyms):
                detected_crop = canonical.capitalize()
                break
        
        if not detected_crop:
            if crop_override and crop_override != "General":
                detected_crop = crop_override
            else:
                detected_crop = "General"

        # Symptom / Problem extraction
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
        if any(kw in text_lower for kw in ["yield", "which crop", "crop to sow", "काय पिक घ्यावे", "कोणते पीक", "कौन सी फसल", "उत्पादन", "उत्पन्न", "लागवड"]):
            intent = "CROP_SELECTION"
        elif any(kw in text_lower for kw in ["भाव", "बाजार", "market", "price", "मंडी", "दर", "किंमत", "rate"]):
            intent = "MARKET"
        elif any(kw in text_lower for kw in ["योजना", "अनुदान", "scheme", "subsidy", "विमा", "insurance", "pm-kisan"]):
            intent = "SCHEMES"
        elif detected_symptoms or any(kw in text_lower for kw in ["कीड", "कीड़ा", "रोग", "डिजीज", "disease", "pest", "अळी", "इल्ली", "बुरशी", "फंगस"]):
            intent = "PEST_DISEASE"
        elif any(kw in text_lower for kw in ["फवारणी", "स्प्रे", "मात्रा", "dose", "दवा", "स्प्रे करें", "क्या डालें", "काय टाकावे", "औषध"]):
            intent = "INPUT_USAGE"
        elif any(kw in text_lower for kw in ["पाणी", "सिंचाई", "irrigation", "पाणी कधी", "कब पानी"]):
            intent = "IRRIGATION"
        elif any(kw in text_lower for kw in ["पेरणी", "बुआई", "sowing", "बोवणी", "कब बोएं", "कधी पीक"]):
            intent = "SOWING"
        elif any(kw in text_lower for kw in ["मौसम", "हवामान", "rain", "पाऊस", "weather", "बारिश"]):
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