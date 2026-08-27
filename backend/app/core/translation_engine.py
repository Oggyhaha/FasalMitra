import httpx
import os
from backend.app.config import settings

class TranslationEngine:
    async def translate(self, text: str, target_lang: str) -> str:
        """
        Translates grounded answer into target regional language using AI4Bharat IndicTrans2 model / API.
        If text is already generated in target language, returns text cleanly without modifying dynamic content.
        Supported languages: mr (Marathi), hi (Hindi), gu (Gujarati), en (English)
        """
        if not text or not target_lang or target_lang == "auto":
            return text

        # If AI4Bharat IndicTrans2 endpoint is configured in environment
        indic_endpoint = settings.INDIC_TRANS2_ENDPOINT or os.getenv("INDIC_TRANS2_ENDPOINT", "")
        if indic_endpoint:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        indic_endpoint,
                        json={
                            "inputs": text,
                            "src_lang": "mr",
                            "tgt_lang": target_lang
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("translated_text", text)
            except Exception as e:
                print(f"[IndicTrans2] Live API fallback: {e}", flush=True)

        # Return synthesized text directly to preserve exact LLM language output
        return text

translation_engine = TranslationEngine()
