import os
import httpx
import re
from typing import List, Dict, Optional
from backend.app.schemas.schemas import EvidenceChunk
from backend.app.config import settings

CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest"
]


class GroundedLLMGenerator:
    async def generate_response(
        self,
        user_query: str,
        evidence: List[EvidenceChunk],
        crop: str,
        stage_name: str,
        weather_info: str,
        language: str = "mr",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generates comprehensive, grounded agronomist advisory strictly utilizing
        retrieved ICAR/KVK/KCC evidence context via modern Gemini Flash LLM.
        """
        evidence_text = "\n\n".join([f"Official Evidence [{e.authority} - {e.title}]:\n{e.text}" for e in evidence])
        
        history_text = ""
        if conversation_history:
            history_text = "\nRecent Conversation History:\n" + "\n".join(
                [f"{h.get('sender', 'FARMER')}: {h.get('text', '')}" for h in conversation_history[-4:]]
            ) + "\n"

        lang_names = {
            "mr": "Marathi (मराठी)",
            "hi": "Hindi (हिंदी)",
            "en": "English",
            "gu": "Gujarati (ગુજરાતી)"
        }
        target_lang_name = lang_names.get(language, "Marathi (मराठी)")

        system_prompt = (
            f"You are FasalMitra (फसलमित्र), an expert senior agricultural advisor and ICAR/KVK certified agronomist helping Indian farmers.\n\n"
            f"MANDATORY INSTRUCTIONS:\n"
            f"1. LANGUAGE: You MUST write your entire response fluently and warmly in {target_lang_name}.\n"
            f"2. GROUNDING: Base your diagnosis, treatment, varieties, and dosages strictly on the official agricultural evidence provided below.\n"
            f"3. THOROUGHNESS & DEPTH:\n"
            f"   - Explain the CAUSE (Why this happens - e.g. pest lifecycle, nutrient deficiency, weather condition).\n"
            f"   - Detail the ACTION PLAN / PROCESS (Step 1, Step 2, Step 3 clearly formatted with bullet points).\n"
            f"   - Include APPROVED REMEDIES & EXACT DOSAGES (e.g. chemical/biological names and exact ml/g per liter or per acre/hectare as stated in evidence).\n"
            f"   - Add WEATHER & SAFETY PRECAUTIONS (e.g. spray timing, protective equipment, waiting before harvest).\n"
            f"4. FORMATTING: Use clean bullet points, bold key terms, and maintain a respectful, empathetic tone for the farmer.\n\n"
            f"Farmer Context:\n"
            f"• Crop: {crop}\n"
            f"• Crop Stage: {stage_name}\n"
            f"• Current Weather: {weather_info}\n"
            f"{history_text}\n"
            f"Official Agricultural Evidence (ICAR/KVK/KCC):\n"
            f"{evidence_text}\n\n"
            f"Farmer's Question: {user_query}\n\n"
            f"Deliver a complete, high-quality, practical agronomist advisory in {target_lang_name}:"
        )

        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

        # 1. Live Google Gemini API Integration with Multi-Model Fallback
        if gemini_key:
            async with httpx.AsyncClient(timeout=8.0) as client:
                for model_name in CANDIDATE_MODELS:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                    payload = {
                        "contents": [{"parts": [{"text": system_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 1024
                        }
                    }
                    try:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            res_data = resp.json()
                            candidates = res_data.get("candidates", [])
                            if candidates:
                                generated_text = candidates[0]["content"]["parts"][0]["text"].strip()
                                return generated_text
                        else:
                            print(f"[LLMGenerator] {model_name} HTTP {resp.status_code}, trying next model...", flush=True)
                    except Exception as e:
                        print(f"[LLMGenerator] {model_name} error: {e}, trying next model...", flush=True)

        # 2. Deterministic High-Quality Fallback if API is offline
        return self._generate_deterministic_fallback(evidence, user_query, language, crop, stage_name)

    def _generate_deterministic_fallback(
        self,
        evidence: List[EvidenceChunk],
        user_query: str,
        language: str,
        crop: str,
        stage_name: str
    ) -> str:
        """Deterministic synthesis directly extracted from verified official evidence text."""
        if not evidence:
            no_info_msg = {
                "mr": "या प्रश्नावर आमच्याकडे अधिकृत पुरावा उपलब्ध नाही. कृपया जवळच्या कृषी विज्ञान केंद्राशी संपर्क साधावा.",
                "hi": "इस प्रश्न पर हमारे पास आधिकारिक प्रमाण उपलब्ध नहीं है। कृपया नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।",
                "en": "Insufficient evidence to answer this question. Please consult your nearest Krishi Vigyan Kendra.",
                "gu": "આ પ્રશ્ન પર અમારી પાસે અધિકૃત પુરાવા નથી. કૃપા કરીને નજીકના કૃષિ વિજ્ઞાન કેન્દ્રનો સંપર્ક કરો."
            }
            return no_info_msg.get(language, no_info_msg["en"])

        top_evidence = evidence[0]
        # Clean up evidence text to be farmer-readable
        clean_text = top_evidence.text
        # Remove CSV prefix artifacts if present
        clean_text = re.sub(r'Farmer Question:.*?\n', '', clean_text)
        clean_text = re.sub(r'Official KCC Agronomist Recommendation:\s*', '', clean_text)
        clean_text = clean_text.strip()

        lang_headers = {
            "mr": f"🌱 **फसलमित्र कृषी सल्ला ({crop} - {top_evidence.title})**\n\n📌 **अधिकृत शिफारस ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **टीप:** फवारणी करताना जमिनीत पुरेशी ओलावा असावी आणि पाऊस पडण्याची शक्यता असल्यास फवारणी पुढे ढकलावी.",
            "hi": f"🌱 **फसलमित्र कृषि परामर्श ({crop} - {top_evidence.title})**\n\n📌 **आधिकारिक संस्तुति ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **सुझाव:** छिड़काव के समय खेत में पर्याप्त नमी रखें और मौसम साफ होने पर ही छिड़काव करें।",
            "en": f"🌱 **FasalMitra Agricultural Advisory ({crop} - {top_evidence.title})**\n\n📌 **Official Recommendation ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **Precaution:** Ensure adequate soil moisture during application and avoid spraying before rainfall.",
            "gu": f"🌱 **ફસલમિત્ર કૃષિ સલાહ ({crop} - {top_evidence.title})**\n\n📌 **અધિકૃત ભલામણ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **સૂચના:** દવા છાંટતી વખતે જમીનમાં ભેજ હોવો જરૂરી છે."
        }

        return lang_headers.get(language, lang_headers["en"])

llm_generator = GroundedLLMGenerator()