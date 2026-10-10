"""
Cognitive Zero-Shot Semantic LLM Parser for FasalMitra.
Leverages modern Multilingual Gemini Flash LLM to parse complex, conversational,
adversarial, or dialect-rich farmer queries into structured agricultural entities.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings

class SemanticLLMParser:
    def __init__(self):
        self.model_name = "gemini-flash-lite-latest"
        self.timeout_sec = 4.0

    async def parse_semantic_query(self, query: str, crop_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Parses query using Gemini Flash zero-shot schema.
        Returns structured dict or None if API is offline/unavailable.
        """
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return None

        prompt = f"""You are an expert Indian Agronomist AI system.
Analyze the following farmer's query and output a strict JSON object with:
- "crop": Canonical crop name (e.g., "Cotton", "Rice", "Wheat", "Soybean", "Chilli", "Tomato", "Groundnut", "General")
- "target": Canonical agricultural pest, disease, or problem ID (e.g. "BOLL_ROT", "WHITEFLY", "ROOT_ROT", "BLAST", "POWDERY_MILDEW", "TIKKA", "YELLOW_MOSAIC", "PINK_BOLLWORM", or null if out-of-domain/abstention/malformed)
- "intent": Granular intent ("DIAGNOSIS_SYMPTOMS", "MANAGEMENT_CONTROL", "DISEASE_CAUSE", "PLANT_PROTECTION", "MARKET", "SCHEMES", "GENERAL_CROP")
- "negated_targets": List of targets explicitly negated, revoked, or attributed only to neighbors/distractor documents/injections
- "reasoning": 1-sentence explanation

Farmer Query: "{query}"

Output ONLY the JSON object, nothing else.
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_json = candidates[0]["content"]["parts"][0]["text"].strip()
                        parsed = json.loads(text_json)
                        return {
                            "crop": parsed.get("crop"),
                            "target": parsed.get("target"),
                            "intent": parsed.get("intent", "GENERAL_CROP"),
                            "negated_targets": parsed.get("negated_targets", []),
                            "reasoning": parsed.get("reasoning", "")
                        }
        except Exception as e:
            # Silently fallback to local ontology without crashing
            pass

        return None

semantic_llm_parser = SemanticLLMParser()
