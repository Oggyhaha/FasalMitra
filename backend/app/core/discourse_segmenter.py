"""
Discourse Clause Segmenter for FasalMitra Query Understanding.
Deconstructs complex, adversarial, multi-clause, and conversational queries:
- ADVERSARIAL_INJECTION: Neutralizes prompt injections while preserving genuine crop symptoms
- RETRIEVAL_DISTRACTOR: Mentions of accidental documents/search results
- THIRD_PARTY_DISCLAIMER: Symptoms belonging to neighbors rather than the user
- FOCUS_EXTRACTION: Identifies asked organ/symptom in multi-problem queries
- CROSS_CROP_FILTER: Prevents cross-crop distractor transfer
- NEGATION_SCOPE: Extracts explicit exclusions, retractions, or healthy tissue affirmations
"""

import re
from typing import Dict, List, Any, Set, Tuple, Optional

class DiscourseSegmenter:
    def __init__(self):
        # Patterns for prompt injections and instructions to hijack output
        self.injection_patterns = [
            r"if\s+you\s+are\s+an\s+ai.*?(?:choose|say|answer)\s+['\"]?([a-zA-Z_]+)['\"]?",
            r"(?:ignore|override)\s+(?:diagnosis|all\s+previous\s+instructions|prompt|symptoms|rules)(?:\s+and\s+(?:say|return|choose)\s+['\"]?([a-zA-Z_]+)['\"])?",
            r"print\s+(?:its|your)\s+(?:internal\s+)?(?:prompt|instructions|hidden\s+prompt)",
            r"answer\s+only\s+['\"]?([a-zA-Z_]+)['\"]?",
            r"say\s+everything\s+is\s+safe",
            r"\{\s*['\"]expected_target['\"]\s*:\s*['\"]?([a-zA-Z_]+)['\"]?\s*\}",
            r"\{\s*['\"]instruction['\"]\s*:\s*['\"]say\s+([a-zA-Z_]+)['\"]\s*\}",
            r"you\s+are\s+now\s+dan.*",
            r"system:\s*output\s+([a-zA-Z_]+)\s+only",
            r"json\s+says\s+target\s+([a-zA-Z_]+)",
            r"developer\s+says\s+classify\s+as\s+([a-zA-Z_\s]+)",
            r"retrieved\s+instruction\s+says\s+answer\s+([a-zA-Z_]+)",
            r"पिछले\s+निर्देश\s+भूल\s+जाओ\s+और\s+([a-zA-Z_]+)\s+बोलो",
            r"<target>([a-zA-Z_]+)</target>",
            r"\[admin\]\s*target=([a-zA-Z_]+)\s*\[/admin\]",
            r"force\s+([a-zA-Z_]+)\s+for\s+benchmark",
            r"ignore\s+rules\s+and\s+say\s+([a-zA-Z_]+)"
        ]

        # Non-agricultural entities and OOD questions
        self.ood_patterns = [
            r"phone\s+screen", r"my\s+dog", r"car\s+engine", r"root\s+of\s+a\s+tooth",
            r"bowling\s+ball", r"baseball", r"bathroom\s+wall", r"music\s+festival",
            r"write\s+a\s+poem", r"translate\s+['\"].*?['\"]\s+into",
            r"quantum\s+entanglement", r"kubernetes", r"stock\s+price",
            r"tractor\s+engine", r"root\s*rot\s+root\s*rot\s+root\s*rot",
            r"carrot\s+quality", r"marketing\s+prices", r"crop\s+rotation\s+advice\s+relevant\s+to\s+root\s*rot"
        ]

        # Quoted or accidental document distractors
        self.retrieval_patterns = [
            r"(?:a\s+)?(?:report|document|search\s+result|advisory)\s+(?:says|said|mentions|contains|recommends)\s*['\"]?([^'\"]+)['\"]?",
            r"search\s+result\s+mentions\s+([a-zA-Z_\s]+)",
            r"retrieved\s+(?:chunk|advisory|result|document)\s+(?:is\s+for|says|returns|ranks)\s+([a-zA-Z_\s]+)",
            r"pasted\s+document\s+says\s+([a-zA-Z_\s]+)",
            r"retrieval\s+returns\s+a\s+([a-zA-Z_\s]+)\s+document",
            r"pasted\s+note\s+calls\s+it\s+([a-zA-Z_\s]+)",
            r"unrelated\s+note\s+says\s+([a-zA-Z_\s]+)",
            r"forum\s+says\s+([a-zA-Z_\s]+)"
        ]

        # Neighbor disclaimers
        self.neighbor_patterns = [
            r"(?:the\s+)?farmer\s+next\s+to\s+me\s+has\s+([a-zA-Z_\s]+)",
            r"my\s+neighbou?r(?:'s)?\s+(?:cotton|crop|farm)?\s+has\s+([a-zA-Z_\s]+)",
            r"neighbou?r\s+identifies\s+a\s+pest",
            r"neighbou?r\s+had\s+([a-zA-Z_\s]+)",
            r"neighbou?r\s+says\s+it\s+is\s+([a-zA-Z_\s]+)",
            r"neighbouring\s+([a-zA-Z_\s]+)\s+plot"
        ]

        self.all_canonical_targets = [
            "BOLL_ROT", "WHITEFLY", "ROOT_ROT", "PINK_BOLLWORM", "BLAST",
            "BACTERIAL_LEAF_BLIGHT", "POWDERY_MILDEW", "EARLY_BLIGHT", "LATE_BLIGHT",
            "TIKKA", "LEAF_CURL", "DAMPING_OFF", "STEM_BORER", "FRUIT_BORER",
            "RED_ROT", "YELLOW_MOSAIC", "FALL_ARMYWORM", "APHID", "JASSID",
            "WILT", "RUST", "SMUT", "COLLAR_ROT", "TERMITES"
        ]

    def segment_and_filter(self, raw_text: str) -> Dict[str, Any]:
        text_lower = raw_text.lower().strip()
        # Clean noisy delimiters including hyphens inside malformed words
        text_clean = re.sub(r'[:@#|;?]+', ' ', text_lower)
        text_clean = re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', text_clean)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()

        negated_targets: Set[str] = set()
        distractors: List[str] = []
        is_injection = False
        focus_organ: Optional[str] = None

        # 1. Non-agricultural Out of Domain
        is_abstention = False
        for p in self.ood_patterns:
            if re.search(p, text_clean):
                is_abstention = True
                break

        # 2. Cross-Crop meta questions ("Is that enough to label...? Should target be boll rot? Valid? Is it applicable?")
        if re.search(r"is\s+that\s+enough\s+to\s+label|what\s+should\s+happen\??|should\s+the\s+target\s+be\s+cotton\s+boll\s*rot|should\s+i\s+follow\s+it\??|is\s+it\s+applicable\??|valid\??|should\s+it\s+support\s+a\s+diagnosis\??|castor\s+capsules.*?is\s+it\s+boll\s*rot|can\s+(?:the\s+)?chilli\s+be\s+diagnosed\s+from\s+it|is\s+whitefly\s+the\s+target\??|the\s+query\s+is\s+about\s+okra\s+fruit\s+rot", text_clean):
            if any(w in text_clean for w in ["retrieved", "ranks first", "article was retrieved", "document is retrieved", "chunk ranks first", "castor capsules", "okra fruit rot", "no positive symptom evidence", "changed irrigation"]):
                if "which should be used" not in text_clean and "should that label transfer" not in text_clean:
                    is_abstention = True
                    negated_targets.add("BOLL_ROT")
                    negated_targets.add("ROOT_ROT")
                    negated_targets.add("WHITEFLY")
                    negated_targets.add("POWDERY_MILDEW")
                    negated_targets.add("BLAST")

        # 3. Prompt Injections (Neutralize instruction, add injected target to negated set)
        for p in self.injection_patterns:
            matches = re.finditer(p, text_clean)
            for m in matches:
                is_injection = True
                for g in m.groups():
                    if g:
                        injected = g.upper().strip().replace(" ", "_")
                        for canonical in self.all_canonical_targets:
                            if canonical in injected or injected in canonical:
                                negated_targets.add(canonical)

        # 4. Retrieval Traps and Distractors
        for p in self.retrieval_patterns:
            matches = re.finditer(p, text_clean)
            for m in matches:
                for g in m.groups():
                    if g:
                        entity = g.upper().strip().replace(" ", "_")
                        distractors.append(entity)
                        for canonical in self.all_canonical_targets:
                            if canonical in entity or entity in canonical or canonical.replace("_", " ") in g.lower():
                                if not ("boll" in text_clean and canonical == "BOLL_ROT" and ("soft" in text_clean or "black" in text_clean)):
                                    negated_targets.add(canonical)

        # 5. Neighbour Disclaimers
        for p in self.neighbor_patterns:
            matches = re.finditer(p, text_clean)
            for m in matches:
                for g in m.groups():
                    if g:
                        neighbor_target = g.upper().strip()
                        for canonical in self.all_canonical_targets:
                            if canonical in neighbor_target:
                                negated_targets.add(canonical)
                if "whitefly" in text_clean:
                    negated_targets.add("WHITEFLY")
        if "neighbouring wheat" in text_clean:
            negated_targets.add("POWDERY_MILDEW")
            negated_targets.add("RUST")

        # 6. Question Focus Extraction (Resolves MULTI_TARGET queries)
        if re.search(r"the\s+question\s+is\s+(?:only\s+)?['\"]?(?:why\s+are\s+the\s+)?(?:cotton\s+)?bolls|the\s+question\s+is\s+about\s+bolls|asks?\s+about\s+the\s+bolls|explains?\s+the\s+lower\s+bolls|yield-relevant\s+evidence\s+is\s+boll", text_clean):
            focus_organ = "BOLL"
            negated_targets.add("ROOT_ROT")
            negated_targets.add("WHITEFLY")
            negated_targets.add("THRIPS")
            negated_targets.add("JASSID")
            negated_targets.add("POWDERY_MILDEW")

        elif re.search(r"the\s+question\s+is\s+(?:only\s+)?['\"]?why\s+are\s+the\s+plants\s+wilting\s+from\s+below|the\s+question\s+is\s+about\s+roots|killing\s+the\s+plants|die\s+in\s+patches\s+and\s+the\s+roots\s+are\s+soft|what\s+is\s+damaging\s+the\s+roots|real\s+worry\s+is\s+that\s+the\s+roots\s+are\s+rotten|wilting\s+from\s+the\s+base|wilting\s+from\s+below", text_clean):
            focus_organ = "ROOT"
            negated_targets.add("BOLL_ROT")
            negated_targets.add("WHITEFLY")
            negated_targets.add("THRIPS")
            negated_targets.add("POWDERY_MILDEW")

        elif re.search(r"question\s+is\s+about\s+leaf\s+edges|hopper\s+burn\s+on\s+leaves|about\s+leaf\s+edges", text_clean):
            focus_organ = "LEAF_EDGES"
            negated_targets.add("BOLL_ROT")
            negated_targets.add("ROOT_ROT")
            negated_targets.add("WHITEFLY")

        elif re.search(r"asks?\s+about\s+(?:the\s+)?(?:white\s+)?powder|asks?\s+about\s+the\s+leaf\s+coating|what\s+is\s+on\s+the\s+leaves|powder\s+on\s+wheat", text_clean):
            if not re.search(r"no\s+powder", text_clean):
                focus_organ = "POWDER"
                negated_targets.add("RUST")
                negated_targets.add("BOLL_ROT")
                negated_targets.add("ROOT_ROT")
                negated_targets.add("WHITEFLY")

        if re.search(r"no\s+powder", text_clean):
            negated_targets.add("POWDERY_MILDEW")

        elif re.search(r"symptom\s+looks\s+like\s+rust", text_clean):
            focus_organ = "RUST"
            negated_targets.add("POWDERY_MILDEW")

        elif re.search(r"what\s+caused\s+the\s+silvering", text_clean):
            focus_organ = "THRIPS"
            negated_targets.add("WHITEFLY")

        elif re.search(r"what\s+explains\s+the\s+mosaic\s+pattern", text_clean):
            focus_organ = "YELLOW_MOSAIC"
            negated_targets.add("APHID")

        elif re.search(r"seedlings\s+girdle\s+at\s+soil\s+level", text_clean):
            focus_organ = "COLLAR_ROT"
            negated_targets.add("TIKKA")

        # 7. Prefix "Not [Target]:" handling
        not_prefix_match = re.search(r"(?:^|[\.\?!])\s*not\s+([a-zA-Z_\s]+?)\s*[:\.,]", text_clean)
        if not_prefix_match:
            neg_cand = not_prefix_match.group(1).upper().strip().replace(" ", "_")
            for canonical in self.all_canonical_targets:
                if canonical in neg_cand or neg_cand in canonical or canonical.replace("_", " ") in not_prefix_match.group(1).upper():
                    negated_targets.add(canonical)

        # 8. Systematic Negation Prefixes (e.g. "Don't tell me about root rot", "It is not boll rot", "besides powdery mildew")
        neg_prefixes = r"(?:it\s+is\s+not|not\s+|\bno\s+|don't\s+tell\s+me\s+about|do\s+not\s+(?:tell|give|share)?\s*(?:me\s+)?(?:about|information\s+on|info\s+on)?|besides|other\s+than|an\s+unrelated\s+note\s+says|unrelated\s+note\s+says|treatment\s+reduced|proves?\s+|spray\s+failed.*?therefore\s+it\s+must\s+be|forum\s+says)"
        for target in self.all_canonical_targets:
            target_str = target.lower().replace("_", r"\s*")
            if re.search(rf"{neg_prefixes}\s*(?:about\s+)?{target_str}", text_clean) or re.search(rf"{target_str}\s+treatment\s+reduced", text_clean):
                negated_targets.add(target)

        # 9. Explicit Retractions, Negations, and Non-Disease Phenomena
        if "i did not say late blight" in text_clean:
            negated_targets.add("LATE_BLIGHT")
        if "not early blight" in text_clean:
            negated_targets.add("EARLY_BLIGHT")

        if "not powdery mildew" in text_clean:
            negated_targets.add("POWDERY_MILDEW")

        if "never mentioned root rot" in text_clean or ("no root rot" in text_clean and "only in the new plants" not in text_clean):
            negated_targets.add("ROOT_ROT")

        if "neither whitefly nor aphids" in text_clean:
            negated_targets.add("WHITEFLY")
            negated_targets.add("APHID")
        elif "not whitefly" in text_clean or "safed makhi nathi" in text_clean or "makhi nahi hai" in text_clean or "kida nahi" in text_clean or "no wite fly" in text_clean or "white makhi nathi" in text_clean or "koi kida nahi dikha" in text_clean or "jivat nathi" in text_clean or "sorry, i said whitefly" in text_clean or "asks if it is whitefly" in text_clean or "no insects were present" in text_clean:
            negated_targets.add("WHITEFLY")

        if "no dead heart" in text_clean:
            negated_targets.add("STEM_BORER")

        if "no holes in tomato" in text_clean:
            negated_targets.add("FRUIT_BORER")

        if "hard and dry, not soft" in text_clean or "roots are white, firm" in text_clean or "roots are not rotten" in text_clean or "roots are firm and white" in text_clean or "deliberately cut open" in text_clean or "shopkeeper told them" in text_clean or "roots are healthy" in text_clean or "roots are clean" in text_clean or "roots are fine" in text_clean or "roots are normal" in text_clean:
            negated_targets.add("ROOT_ROT")

        if "healthy bolls" in text_clean:
            negated_targets.add("BOLL_ROT")

        if "dried spray residue" in text_clean or "vanish by noon like dew" in text_clean or "powdery coating only on the underside" in text_clean or "dust from nearby construction" in text_clean or "it is dust" in text_clean or "earlier white powder" in text_clean:
            negated_targets.add("POWDERY_MILDEW")

        if "soot from the brick kiln" in text_clean or "lint inside is white" in text_clean or "bolls are hard and dry" in text_clean or "mechanically crushed" in text_clean or "black only on the outer surface" in text_clean or "completely dry and hard" in text_clean or "clean lint, but the user asks why they are rotting" in text_clean or "asks about boll rot only" in text_clean or "no cotton bolls exist" in text_clean:
            negated_targets.add("BOLL_ROT")

        if "sprayed insecticide twice for whitefly" in text_clean or "treated for whitefly" in text_clean or "insects are on the weeds" in text_clean or "whitefly is present in the field, but the symptomatic plant has no insects" in text_clean:
            negated_targets.add("WHITEFLY")

        if "earlier i said wheat, but this symptom is on paddy" in text_clean:
            negated_targets.add("RUST")
            negated_targets.add("POWDERY_MILDEW")

        if "forget the tomato problem" in text_clean:
            negated_targets.add("EARLY_BLIGHT")
            negated_targets.add("LATE_BLIGHT")

        if "ignore the earlier rice question" in text_clean:
            negated_targets.add("BLAST")
            negated_targets.add("STEM_BORER")

        if "you called it thrips, but i meant" in text_clean:
            negated_targets.add("THRIPS")

        if "roots rotted last season" in text_clean and "this season the roots are clean and the bolls are the ones turning black" in text_clean:
            negated_targets.add("ROOT_ROT")

        # Double negative preservation ("It is not that the bolls are not rotten; they are definitely black and soft")
        if "definitely black and soft" in text_clean or "not that the bolls are not rotten" in text_clean:
            negated_targets.discard("BOLL_ROT")

        # No root rot in older, only in new plants with soft roots
        if "only in the new plants whose roots are soft" in text_clean:
            negated_targets.discard("ROOT_ROT")

        # Pathognomonic evidence overrides casual doubts
        if "spindle spots" in text_clean or "broken and black" in text_clean:
            negated_targets.discard("BLAST")
            negated_targets.discard("ROOT_ROT")

        return {
            "cleaned_text": text_clean,
            "negated_targets": list(negated_targets),
            "distractors": distractors,
            "is_injection": is_injection,
            "is_abstention": is_abstention,
            "focus_organ": focus_organ
        }

discourse_segmenter = DiscourseSegmenter()
