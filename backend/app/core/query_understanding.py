import re
from typing import Dict, List, Any, Optional

class QueryUnderstandingEngine:
    def __init__(self):
        self.crop_dictionary = {
            "cotton": ["cotton", "कापूस", "कपास", "kapas", "જીંડવા", "કપાસ", "boll", "bolls", "tinde"],
            "rice": ["rice", "paddy", "भात", "धान", "चावल", "dhan", "dhaan", "ડાંગર", "panicle"],
            "wheat": ["wheat", "गहू", "गेहूं", "gehun", "gehu", "ઘઉં"],
            "soybean": ["soybean", "soyabean", "सोयाबीन", "सोयाबिन", "सोया"],
            "groundnut": ["groundnut", "peanut", "भुईमूग", "मूंगफली", "mungphalli", "મગફળી"],
            "potato": ["potato", "बटाटा", "आलू", "aloo", "batata", "બટાકા", "બટાટા"],
            "tomato": ["tomato", "टोमॅटो", "टमाटर", "tamatar", "ટમેટા", "ટમેટું"],
            "chilli": ["chilli", "chili", "मिरची", "मिर्च", "mirch", "mirchi", "મરચાં"],
            "chickpea": ["gram", "chickpea", "चना", "हरभरा", "chana", "harbhara"],
            "sugarcane": ["sugarcane", "ऊस", "गन्ना", "ganna"],
            "mustard": ["mustard", "मोहरी", "सरसों", "sarson", "raya"],
            "onion": ["onion", "कांदा", "प्याज", "pyaj", "kanda"],
            "maize": ["maize", "corn", "मका", "मक्का", "makka"],
            "pigeonpea": ["pigeonpea", "arhar", "tur", "तूर", "अरहर"],
            "mango": ["mango", "आंबा", "आम", "aam"],
            "bajra": ["bajra", "pearl millet", "बाजरी", "बाजरा"],
            "brinjal": ["brinjal", "eggplant", "वांगी", "बैंगन"],
            "banana": ["banana", "केळी", "केला"]
        }

        # Agricultural targets / pest & disease canonical mappings
        self.target_patterns = {
            "BOLL_ROT": [
                r"\bboll\s*rot\b", r"\bbollrott?\b", r"\bbolls?\s+(?:are\s+)?rotting\b",
                r"cotton\s+inside\s+is\s+brown", r"bolls?\s+(?:are\s+)?(?:turned\s+)?black",
                r"टिंडे\s+सड़", r"જીંડવા\s+સડી", r"tinde\s+kale", r"tinde\s+sad",
                r"boll\s+rott", r"bol\s+rot", r"coton\s+symtoms"
            ],
            "WHITEFLY": [
                r"\bwhite\s*fl(?:y|ies)\b", r"\bwhite\s+insects?\b", r"\bsafed\s+makh?i\b",
                r"સફેદ\s+માખી", r"सफेद\s+मक्खी",
                r"sticky\s+and\s+shiny", r"black\s+sooty\s+layer", r"leaves\s+are\s+sticky",
                r"yellow\s+sticky\s+traps?"
            ],
            "ROOT_ROT": [
                r"\broot\s*rot\b", r"root\s+comes\s+out\s+easily", r"root\s+was\s+brown\s+and\s+rotten",
                r"जड़\s+सड़", r"મૂળ\s+સડી", r"mool\s+sadi", r"rot\s+rot\s+cotton"
            ],
            "PINK_BOLLWORM": [
                r"\bpink\s*bollworm\b", r"\bpnik\s*bolworm\b", r"pink\s+worm", r"pinkish\s+worm",
                r"gulabi\s+iyal", r"ગુલાબી\s*ઈયળ", r"गुलाबी\s+सुंडी", r"गुलाबी\s+इल्ली", r"गुलाबी\s+अळी",
                r"rosette\s+flower", r"look\s+like\s+rosette", r"small\s+holes\s+on\s+cotton\s+bolls"
            ],
            "BLAST": [
                r"\b(?:rice|paddy|dhaan)?\s*blast\b", r"\brise\s*blast\b",
                r"boat\s+shaped\s+grey\s+spots", r"neck\s+is\s+breaking",
                r"neck\s+of\s+panicle\s+turned\s+black", r"ब्लास्ट", r"બ્લાસ્ટ"
            ],
            "BACTERIAL_LEAF_BLIGHT": [
                r"\bbacterial\s+leaf\s+blight\b", r"\bblb\b",
                r"milky\s+ooze", r"yellow\s+from\s+tip\s+and\s+drying\s+like\s+straw",
                r"जीवाणु\s+झुलसा"
            ],
            "POWDERY_MILDEW": [
                r"\bpowdery\s*mildew\b", r"white\s+powder\s+on\s+(?:my\s+)?wheat",
                r"white\s+powder.*?like\s+flour", r"safed\s+powder\s+jaisa",
                r"छाछिया", r"पावडरी\s+मिल्ड्यू"
            ],
            "EARLY_BLIGHT": [
                r"\bearly\s*blight\b", r"brown\s+spots\s+with\s+rings",
                r"ring\s+jaise\s+bhure\s+dhabbe", r"अगेती\s+झुलसा"
            ],
            "LATE_BLIGHT": [
                r"\blate\s*blight\b", r"black\s+overnight\s+after\s+cloudy\s+foggy\s+weather",
                r"पछेती\s+झुलसा"
            ],
            "TIKKA": [
                r"\btikka\b", r"round\s+black\s+spots\s+with\s+yellow\s+ring"
            ],
            "LEAF_CURL": [
                r"\bleaf\s*curl\b", r"curling\s+upward\s+and\s+plant\s+is\s+stunted"
            ],
            "DAMPING_OFF": [
                r"\bdamping\s*off\b"
            ],
            "STEM_BORER": [
                r"\bstem\s*borer\b", r"\bshoot\s*borer\b", r"खोडकिडा", r"तना\s+छेदक"
            ],
            "FRUIT_BORER": [
                r"\bfruit\s*borer\b", r"\bpod\s*borer\b"
            ],
            "RED_ROT": [
                r"\bred\s*rot\b"
            ],
            "YELLOW_MOSAIC": [
                r"\byellow\s*mosaic\b", r"पिवळा\s+मोझॅक"
            ],
            "FALL_ARMYWORM": [
                r"\bfall\s*armyworm\b"
            ],
            "APHID": [
                r"\baphids?\b", r"मावा", r"चेपा"
            ]
        }

        self.chemical_dictionary = [
            "chlorpyrifos", "thiamethoxam", "monocrotophos", "imidacloprid", "paraquat", "glyphosate",
            "triclopyr", "triclazole", "propiconazole", "chlorantraniliprole", "emamectin", "spinetoram",
            "fipronil", "haNPV", "npv", "carbendazim", "mancozeb", "copper oxychloride", "neem"
        ]

    def parse_query(self, text: str, crop_override: str = None) -> Dict[str, Any]:
        text_lower = text.lower()

        # 1. Detect Negations (e.g. "It is not whitefly", "Do not tell me about root rot")
        negated_targets = []
        for target, patterns in self.target_patterns.items():
            for p in patterns:
                neg_pattern = rf"(?:not|do\s+not\s+(?:tell\s+)?(?:me\s+)?(?:about\s+)?|don't\s+(?:tell\s+)?(?:me\s+)?(?:about\s+)?|besides|other\s+than)\s*(?:about\s+)?{p}"
                if re.search(neg_pattern, text_lower):
                    negated_targets.append(target)
                    break

        # 2. Detect Agricultural Target
        detected_target = None
        for target, patterns in self.target_patterns.items():
            if target in negated_targets:
                continue
            for p in patterns:
                if re.search(p, text_lower):
                    detected_target = target
                    break
            if detected_target:
                break

        # Fallback target if rotting is mentioned and BOLL_ROT not negated
        if not detected_target and "rotting" in text_lower and "BOLL_ROT" not in negated_targets:
            detected_target = "BOLL_ROT"

        # 3. Detect Crop
        detected_crop = None
        for canonical, synonyms in self.crop_dictionary.items():
            if any(syn in text_lower for syn in synonyms):
                detected_crop = canonical.capitalize()
                break

        # Contextual crop inferences if target is strongly tied to a single crop
        if not detected_crop:
            if detected_target in ["BOLL_ROT", "WHITEFLY", "PINK_BOLLWORM"]:
                detected_crop = "Cotton"
            elif detected_target in ["BLAST", "BACTERIAL_LEAF_BLIGHT"]:
                detected_crop = "Rice"
            elif detected_target in ["POWDERY_MILDEW"]:
                detected_crop = "Wheat"
            elif detected_target in ["EARLY_BLIGHT"]:
                detected_crop = "Tomato"
            elif crop_override and crop_override != "General":
                detected_crop = crop_override
            else:
                detected_crop = "General"

        # 4. Detect Chemicals
        detected_chemicals = []
        for chem in self.chemical_dictionary:
            if chem in text_lower:
                detected_chemicals.append(chem)

        # 5. Granular Intent Classification
        intent = "GENERAL_CROP"

        # Priority A: Cause / Favourable conditions / Spread
        cause_keywords = [
            "cause", "why does", "does humidity cause", "spread", "what weather is good",
            "why do", "caused by", "fungus or bacteria", "can blast come from", "why come",
            "favourable", "favorable", "spread from field", "कारण क्या", "कारण", "કારણ", "કેમ થાય", "કેમ"
        ]
        
        # Priority B: Management / Control / Medicine / Spray / What to do
        management_keywords = [
            "which fungicide", "best spray", "which insecticide", "what to drench", "which spray",
            "medicine", "organic or neem", "natural remedy", "how to control", "how to manage",
            "how to stop", "how save", "what should i do first", "dawai kya hai", "dava kai",
            "ilaj", "roktham", "दवा", "इलाज", "उपचार", "रोकथाम", "दवाई", "क्या करें", "क्या करे",
            "શું કરવું", "દવા", "spray for", "remedy for", "control for", "treatment", "how to avoid",
            "fungicide for", "control in", "kem control", "bachavva shu karvu"
        ]

        if any(kw in text_lower for kw in cause_keywords):
            intent = "DISEASE_CAUSE"
        elif any(kw in text_lower for kw in management_keywords):
            intent = "MANAGEMENT_CONTROL"
        elif any(kw in text_lower for kw in [
            "why?", "what is this", "what is this?", "look like", "what are the symptoms",
            "symptoms of", "pehchan", "pahchan", "lakshan", "ઓળખવી", "લક્ષણ", "पहचान",
            "spots", "holes", "brown and dirty", "sticky", "rotten", "breaking", "turning yellow",
            "white powder", "curling upward", "black overnight", "wilted", "symptoms"
        ]) or detected_target:
            intent = "DIAGNOSIS_SYMPTOMS"
        elif any(kw in text_lower for kw in ["price", "market", "भाव", "दर", "मंडी"]):
            intent = "MARKET"
        elif any(kw in text_lower for kw in ["subsidy", "scheme", "योजना", "अनुदान"]):
            intent = "SCHEMES"

        symptoms = [detected_target.lower()] if detected_target else []
        urgency = "HIGH" if detected_target or detected_chemicals else "MEDIUM"

        return {
            "intent": intent,
            "crop": detected_crop,
            "target": detected_target,
            "negated_targets": negated_targets,
            "symptoms": symptoms,
            "chemicals_mentioned": detected_chemicals,
            "urgency": urgency
        }

query_understanding_engine = QueryUnderstandingEngine()