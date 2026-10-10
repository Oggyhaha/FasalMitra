from typing import Dict, Any, Tuple

class PreSafetyGate:
    def __init__(self):
        self.banned_chemicals = ["monocrotophos", "paraquat", "phorate", "endosulfan", "carbofuran", "methyl parathion", "ddt", "triazophos"]
        self.out_of_domain_keywords = [
            "python", "bitcoin", "crypto", "election", "movie", "cricket", "politics",
            "tell me a joke", "joke about", "cow", "fever in my cow", "cattle", "animal",
            "prime minister", "president", "sort a list", "write a python", "program to sort",
            "ignore previous instructions", "system prompt",
            "highest profit this year", "banned pesticides", "mix different pesticides",
            "football", "bollywood", "song lyrics", "write essay", "homework",
            "actor", "actress", "cinema", "chatgpt", "jailbreak", "stock market investing",
            "dog illness", "goat disease", "buffalo fever", "veterinary injection"
        ]

    def evaluate(self, text: str, structured_query: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Returns: (passed: bool, risk_level: str, failure_reason: str)
        """
        text_lower = text.lower()
        
        # 1. Out of domain check (humor, coding, general knowledge, prompt injection, veterinary)
        if any(kw in text_lower for kw in self.out_of_domain_keywords):
            if "banned pesticides" in text_lower:
                return False, "HIGH", "UNSAFE_BANNED_PESTICIDE_REQUEST"
            if "mix different pesticides" in text_lower:
                return False, "HIGH", "UNSAFE_TANK_MIX_REQUEST"
            return False, "HIGH", "OUT_OF_DOMAIN"

        # 2. Dangerous chemical check
        for chem in structured_query.get("chemicals_mentioned", []):
            if chem in self.banned_chemicals:
                return False, "HIGH", f"HIGH_RISK_BANNED_CHEMICAL_{chem.upper()}"

        # 3. Missing critical context for chemical spray query
        if structured_query.get("intent") == "INPUT_USAGE" and context.get("crop") == "General":
            return False, "MEDIUM", "MISSING_CROP_CONTEXT"

        # Risk level determination
        risk_level = "LOW"
        if structured_query.get("intent") in ["PEST_DISEASE", "MANAGEMENT_CONTROL", "INPUT_USAGE"]:
            risk_level = "MEDIUM"
        if structured_query.get("chemicals_mentioned"):
            risk_level = "HIGH"

        return True, risk_level, "PASSED"

pre_safety_gate = PreSafetyGate()
