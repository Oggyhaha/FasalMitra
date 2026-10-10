"""
Agricultural Diagnostic Ontology & Biological Compatibility Engine for FasalMitra.
Encodes botanical host specificity, plant organ ontology, and pathological sign matrices.
Resolves (Host Crop, Affected Plant Organ, Pathological Sign) -> Diagnostic Target.
"""

import re
from typing import Dict, List, Any, Optional, Set, Tuple

class DiagnosticOntology:
    def __init__(self):
        # Canonical Host Crops and their Vernacular / English synonyms
        self.crop_synonyms = {
            "Cotton": ["cotton", "कापूस", "कपास", "kapas", "kapus", "જીંડવા", "કપાસ", "boll", "bolls", "tinde", "bondya"],
            "Rice": ["rice", "paddy", "भात", "धान", "चावल", "dhan", "dhaan", "ડાંગર", "panicle"],
            "Wheat": ["wheat", "गहू", "गेहूं", "gehun", "gehu", "ઘઉં"],
            "Soybean": ["soybean", "soyabean", "सोयाबीन", "सोयाबिन", "सोया"],
            "Groundnut": ["groundnut", "peanut", "भुईमूग", "मूंगफली", "mungphalli", "મગફળી"],
            "Potato": ["potato", "बटाटा", "आलू", "aloo", "batata", "બટાકા", "બટાટા"],
            "Tomato": ["tomato", "टोमॅटो", "टमाटर", "tamatar", "ટમેટા", "ટમેટું"],
            "Chilli": ["chilli", "chili", "मिरची", "मिर्च", "mirch", "mirchi", "મરચાં"],
            "Chickpea": ["gram", "chickpea", "चना", "हरभरा", "chana", "harbhara"],
            "Sugarcane": ["sugarcane", "ऊस", "गन्ना", "ganna"],
            "Mustard": ["mustard", "मोहरी", "सरसों", "sarson", "raya"],
            "Onion": ["onion", "कांदा", "प्याज", "pyaj", "kanda"],
            "Maize": ["maize", "corn", "मका", "मक्का", "makka"],
            "Pigeonpea": ["pigeonpea", "arhar", "tur", "तूर", "अरहर"],
            "Mango": ["mango", "आंबा", "आम", "aam"],
            "Bajra": ["bajra", "pearl millet", "बाजरी", "बाजरा"],
            "Brinjal": ["brinjal", "eggplant", "वांगी", "बैंगन"],
            "Banana": ["banana", "केळी", "केला"],
            "Okra": ["okra", "bhindi", "भिंडी", "ભીંડા"]
        }

        # Biological Host-Pathogen Compatibility Matrix
        self.crop_allowed_targets = {
            "Cotton": {"BOLL_ROT", "WHITEFLY", "ROOT_ROT", "PINK_BOLLWORM", "APHID", "THRIPS", "JASSID", "WILT", "MEALYBUG", "POWDERY_MILDEW"},
            "Rice": {"BLAST", "BACTERIAL_LEAF_BLIGHT", "STEM_BORER", "SHEATH_BLIGHT", "FALSE_SMUT", "BPH"},
            "Wheat": {"POWDERY_MILDEW", "RUST", "SMUT", "TERMITES", "APHID"},
            "Soybean": {"YELLOW_MOSAIC", "WHITEFLY", "ROOT_ROT", "GIRDLE_BEETLE", "STEM_FLY", "RUST", "CATERPILLAR", "COLLAR_ROT"},
            "Groundnut": {"TIKKA", "ROOT_ROT", "COLLAR_ROT", "APHID", "THRIPS", "WHITE_GRUB"},
            "Tomato": {"EARLY_BLIGHT", "LATE_BLIGHT", "LEAF_CURL", "DAMPING_OFF", "FRUIT_BORER", "WHITEFLY"},
            "Potato": {"LATE_BLIGHT", "EARLY_BLIGHT", "SCAB", "TUBER_MOTH"},
            "Chilli": {"THRIPS", "LEAF_CURL", "DAMPING_OFF", "ANTHRACNOSE", "FRUIT_BORER", "ROOT_ROT", "WHITEFLY"},
            "Chickpea": {"WILT", "ROOT_ROT", "FRUIT_BORER", "COLLAR_ROT"},
            "Sugarcane": {"RED_ROT", "STEM_BORER", "SMUT", "PYRILLA", "RUST"},
            "Maize": {"FALL_ARMYWORM", "STEM_BORER"},
            "Mustard": {"APHID", "WHITE_RUST", "DOWNY_MILDEW"},
            "Onion": {"THRIPS", "PURPLE_BLOTCH", "SMUDGE"},
            "Brinjal": {"FRUIT_BORER", "STEM_BORER", "LITTLE_LEAF"},
            "Okra": {"YELLOW_MOSAIC", "FRUIT_BORER"},
            "Banana": {"WILT", "SIGATOKA"},
            "Mango": {"POWDERY_MILDEW", "ANTHRACNOSE"}
        }

    def detect_host_crop(self, text_clean: str) -> Optional[str]:
        """Detects the primary active crop described by the user."""
        # 1. User explicit focus marker or prefix ("On wheat,", "in wheat", "crop is wheat")
        user_crop_match = re.search(r"(?:user\s+(?:describes|has)\s+|on\s+|in\s+|retrieved\s+for\s+(?:a\s+)?|farmer(?:'s)?\s+crop\s+is\s+|context\s+is\s+|crop\s+is\s+)([a-zA-Z]+)", text_clean)
        if user_crop_match:
            cand = user_crop_match.group(1).lower()
            for canonical, syns in self.crop_synonyms.items():
                if cand in syns or canonical.lower() == cand:
                    return canonical

        # 2. Earliest mentioned crop in text
        earliest_pos = 999999
        detected_crop = None
        for canonical, syns in self.crop_synonyms.items():
            for s in syns:
                pos = text_clean.find(s)
                if pos != -1 and pos < earliest_pos:
                    earliest_pos = pos
                    detected_crop = canonical
        return detected_crop

diagnostic_ontology = DiagnosticOntology()
