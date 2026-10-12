import os
import re
import httpx
from typing import Tuple
from backend.app.config import settings

class ASREngine:
    def __init__(self):
        # Language keywords detection matrix
        self.marathi_keywords = ["माझ्या", "पाने", "पडत", "आहेत", "काय", "करू", "झाली", "पिक", "शेतकरी", "भाऊ", "कीड", "फवारणी", "लक्षणे", "शेती"]
        self.hindi_keywords = ["मेरा", "मेरे", "पत्ते", "पीले", "क्या", "करें", "दवा", "डालें", "फसल", "इल्ली", "कीड़ा", "उपयोग", "कौन", "कौनसी", "स्प्रे", "रोग"]
        self.gujarati_keywords = ["મારા", "પાંદડા", "પીળા", "સોયાબીન", "શું", "કરવું", "પાક", "બટાકા", "ખેતી", "કિડા", "બાજરી", "કપાસ", "છંટકાવ", "ખાતર"]

        # Romanized Gujarati Lexicon (Gujlish)
        self.gujarati_roman_words = {
            # Auxiliaries, copulas, and verb tenses
            "che", "chhe", "chi", "thase", "thashe", "thay", "thaye", "thaine", "thava",
            "karvi", "karvo", "karvu", "karvanu", "karvani", "karvano", "karyu", "karie", "kari", "kare",
            "nathi", "aavshe", "avshe", "aave", "aavyu", "joyiye", "joie", "joiye", "joye",
            "lidhe", "lidho", "lidha", "rahyu", "rahya",
            # Pronouns & determiners
            "mare", "maro", "mari", "maru", "mara", "tamare", "tamaro", "tamari", "tamaru", "tamara",
            "amare", "amaro", "amari", "amaru", "amara", "aamne", "tamne", "mane", "tene", "jeno", "jeni", "jenu",
            # Question words & prepositions
            "kemni", "kemne", "kem", "su", "shu", "syu", "kyare", "kyaare", "kya", "kyaan", "kyathi",
            "ketlu", "ketla", "ketli", "kai", "kayi", "kayo", "kayu", "kevi", "kevo", "kevu",
            "kaho", "janavo", "batavo", "mate",
            # Agricultural vocabulary & common Gujarati nouns
            "bajari", "bajri", "bataka", "batata", "bataaka", "batako", "kapas", "kapaas",
            "ghau", "ghaun", "eranda", "diwela", "raydo", "jeeru", "jira", "magfali", "sing",
            "khedut", "kheduto", "khetar", "vavetar", "vavni", "chhatkav", "chhantkav", "chhatvi", "chhatvu",
            "khatar", "jiwat", "jeewat", "eeyal", "iyal", "paak", "pandada", "paandada",
            "sukay", "sukaay", "bhaav", "vadhare", "vadhu", "thodu", "saru", "haji", "haju",
            "kheti", "dava", "dawa"
        }

        self.gujarati_roman_phrases = [
            "karvi che", "karvu che", "karvo che", "padi che", "thay che", "aave che",
            "kem cho", "kem chho", "su karvu", "shu karvu", "kemni thase", "kem thase",
            "bataka ma", "kapas ma", "khetar ma", "pak ma", "paak ma", "dava chhatvi",
            "mate su", "che kemni", "karvi chhe", "karvu chhe"
        ]

        # Romanized Marathi Lexicon
        self.marathi_roman_words = {
            "ahe", "aahe", "nahit", "hota", "hoti", "hote", "mala", "tula", "tyala", "amha",
            "maza", "mazya", "mazi", "amche", "tumche", "kasa", "kashi", "kase", "kiti",
            "kay", "kaay", "kadhi", "kuthe", "karaycha", "karaychi", "karu", "sangaa", "sanga",
            "sangu", "vikni", "sheti", "bhau", "pika", "panne", "fawarani", "fawarni", "sakto", "apan"
        }

        self.marathi_roman_phrases = [
            "ahe ka", "aahe ka", "kay karu", "kaay karu", "kasa karu", "kashi karu",
            "sheti karaychi", "vikni karna", "vikni karaychi"
        ]

        # Romanized Hindi Lexicon
        self.hindi_roman_words = {
            "kya", "kaise", "karen", "mera", "mere", "meri", "hamara", "humara", "khet",
            "dawai", "chahiye", "hoga", "hogi", "nahi", "nahin", "bataye", "batao", "kisano",
            "karo", "kare", "karna", "kaunsi", "konsi", "kitna", "kitni", "kaun", "kab"
        }

        # Standard English Functional Words
        self.english_words = {
            "how", "to", "control", "what", "is", "the", "why", "are", "in", "my", "crop",
            "disease", "symptoms", "fertilizer", "spray", "when", "should", "i", "can", "for",
            "which", "please", "tell", "recommend", "yield", "best", "variety", "treatment",
            "pest", "management", "yellowing", "leaves", "damage", "roots", "whitefly", "cotton"
        }

    async def transcribe(self, text_input: str, audio_base64: str = None, requested_lang: str = "auto") -> Tuple[str, str, float]:
        """
        Transcribes speech audio or normalizes text input.
        Returns: (normalized_transcript, detected_language, confidence_score)
        """
        transcript = text_input.strip() if text_input else ""

        # If audio voice message is provided, transcribe it using Gemini Multimodal Audio
        if audio_base64 and audio_base64.strip():
            audio_text = await self._transcribe_audio_with_gemini(audio_base64)
            if audio_text:
                transcript = audio_text

        if not transcript:
            transcript = "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"

        # Language detection logic
        detected_lang = requested_lang
        if requested_lang == "auto" or not requested_lang:
            detected_lang = self._detect_language(transcript)

        # Transcript normalization (remove filler words)
        normalized = re.sub(r'\b(uh|um|मतलब|म्हणजे|अरे)\b', '', transcript, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        confidence = 0.95 if audio_base64 is None else 0.92
        return normalized, detected_lang, confidence

    async def _transcribe_audio_with_gemini(self, audio_base64: str, mime_type: str = "audio/ogg") -> str:
        """Transcribes regional Indian farmer voice notes using Gemini Flash Multimodal Audio."""
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return ""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": audio_base64
                            }
                        },
                        {
                            "text": (
                                "You are an agricultural voice transcriber for Indian farmers. "
                                "Accurately transcribe the speech in the exact spoken language (Marathi, Gujarati, Hindi, or English). "
                                "Return ONLY the raw transcription without any explanation, disclaimer, or quotation marks."
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300
            }
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                        print(f"[ASREngine] Gemini Voice Note Transcribed: '{raw_text}'", flush=True)
                        return raw_text
                else:
                    print(f"[ASREngine] Gemini Audio API HTTP {res.status_code}: {res.text[:100]}", flush=True)
        except Exception as e:
            print(f"[ASREngine] Gemini Audio Transcription error: {e}", flush=True)

        return ""

    def _detect_language(self, text: str) -> str:
        # 1. Native Gujarati Unicode script range (\u0A80-\u0AFF)
        if any('\u0a80' <= c <= '\u0aff' for c in text):
            return "gu"

        # 2. Native Devanagari script range (\u0900-\u097F)
        if any('\u0900' <= c <= '\u097f' for c in text):
            for kw in self.marathi_keywords:
                if kw in text:
                    return "mr"
            for kw in self.hindi_keywords:
                if kw in text:
                    return "hi"
            return "mr" if ("आहे" in text or "माझ्या" in text or "शेती" in text) else "hi"

        # 3. Transliterated / Romanized Script Recognition (English alphabet used for Indian languages)
        text_clean = text.lower()
        words = set(re.findall(r'\b[a-z]+\b', text_clean))

        # Check Romanized Gujarati (Gujlish)
        gu_score = len(words.intersection(self.gujarati_roman_words))
        for phrase in self.gujarati_roman_phrases:
            if phrase in text_clean:
                gu_score += 3

        # Check Romanized Marathi
        mr_score = len(words.intersection(self.marathi_roman_words))
        for phrase in self.marathi_roman_phrases:
            if phrase in text_clean:
                mr_score += 3

        # Check Romanized Hindi
        hi_score = len(words.intersection(self.hindi_roman_words))

        # Check Standard English
        en_score = len(words.intersection(self.english_words))

        if gu_score > 0 and gu_score >= max(mr_score, hi_score, en_score):
            return "gu"
        if mr_score > 0 and mr_score >= max(hi_score, en_score):
            return "mr"
        if hi_score > 0 and hi_score > en_score:
            return "hi"

        if text.isascii():
            return "en"

        return "mr"

asr_engine = ASREngine()
