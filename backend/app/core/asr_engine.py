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

        # Standard English Functional Words & Agricultural Vocabulary
        self.english_words = {
            "how", "to", "control", "what", "is", "the", "why", "are", "in", "my", "crop",
            "disease", "symptoms", "fertilizer", "spray", "when", "should", "i", "can", "for",
            "which", "please", "tell", "recommend", "yield", "best", "variety", "treatment",
            "pest", "management", "yellowing", "leaves", "damage", "roots", "whitefly", "cotton",
            "hi", "hello", "hey", "help", "start", "menu", "weather", "passport", "good",
            "morning", "afternoon", "evening", "sir", "madam", "farmer", "agriculture",
            "suggest", "give", "solution", "dose", "rate", "pesticide", "insecticide",
            "fungicide", "wheat", "rice", "paddy", "potato", "tomato", "soybean", "sugarcane",
            "mustard", "groundnut", "chilli", "onion", "garlic", "maize", "corn", "bollworm",
            "rust", "blast", "rot", "blight", "wilt", "mildew", "aphid", "thrips", "caterpillar",
            "worm", "insect", "bug", "field", "soil", "water", "irrigation", "seed", "sowing",
            "harvest", "problem", "issue", "attack", "infection", "prevent", "cure", "stop",
            "kill", "remove", "clean", "mix", "litre", "liter", "acre", "hectare", "gram", "ml", "kg",
            "about", "with", "from", "at", "by", "this", "that", "these", "those", "have", "has",
            "had", "do", "does", "did", "will", "would", "shall", "could", "there", "their", "where"
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
        # 1. Native Script Ranges for all 22 Scheduled Indian Languages + English
        # Gujarati: \u0A80 - \u0AFF
        if any('\u0a80' <= c <= '\u0aff' for c in text):
            return "gu"

        # Gurmukhi (Punjabi): \u0A00 - \u0A7F
        if any('\u0a00' <= c <= '\u0a7f' for c in text):
            return "pa"

        # Telugu: \u0C00 - \u0C7F
        if any('\u0c00' <= c <= '\u0c7f' for c in text):
            return "te"

        # Tamil: \u0B80 - \u0BFF
        if any('\u0b80' <= c <= '\u0bff' for c in text):
            return "ta"

        # Kannada: \u0C80 - \u0CFF
        if any('\u0c80' <= c <= '\u0cff' for c in text):
            return "kn"

        # Malayalam: \u0D00 - \u0D7F
        if any('\u0d00' <= c <= '\u0d7f' for c in text):
            return "ml"

        # Bengali & Assamese: \u0980 - \u09FF
        if any('\u0980' <= c <= '\u09ff' for c in text):
            # Assamese specific characters 'ৰ' (\u09F0) or 'ৱ' (\u09F1)
            if any(c in text for c in ['\u09f0', '\u09f1']):
                return "as"
            return "bn"

        # Odia: \u0B00 - \u0B7F
        if any('\u0b00' <= c <= '\u0b7f' for c in text):
            return "or"

        # Perso-Arabic (Urdu, Kashmiri, Sindhi): \u0600 - \u06FF
        if any('\u0600' <= c <= '\u06ff' for c in text):
            return "ur"

        # Ol Chiki (Santali): \u1C50 - \u1C7F
        if any('\u1c50' <= c <= '\u1c7f' for c in text):
            return "sat"

        # Meetei Mayek (Manipuri): \uABC0 - \uABFF
        if any('\uabc0' <= c <= '\uabff' for c in text):
            return "mni"

        # Devanagari script range (\u0900 - \u097F) (Hindi, Marathi, Sanskrit, Nepali, Konkani, Maithili, Bodo, Dogri)
        if any('\u0900' <= c <= '\u097f' for c in text):
            # Check regional dialect markers
            if any(w in text for w in ["अस्ति", "कृषिः", "भवति", "नमः"]):
                return "sa" # Sanskrit
            if any(w in text for w in ["छ", "छन्", "भयो", "गर्ने", "हाम्रो"]):
                return "ne" # Nepali
            if any(w in text for w in ["आसा", "आहेत", "करचे", "भास"]):
                return "kok" # Konkani
            if any(w in text for w in ["अछि", "छथि", "हमर", "करब"]):
                return "mai" # Maithili
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

        # 1. English takes priority if English keywords dominate
        if en_score > 0 and en_score >= max(gu_score, mr_score, hi_score):
            return "en"

        # 2. Strong Indic transliteration scores (Gujlish, Marathlish, Hinglish)
        if gu_score > 0 and gu_score > max(mr_score, hi_score, en_score):
            return "gu"
        if mr_score > 0 and mr_score > max(hi_score, en_score):
            return "mr"
        if hi_score > 0 and hi_score > max(gu_score, mr_score, en_score):
            return "hi"

        # 3. Default ASCII text with no strong Indic transliterated words is English
        if text.isascii():
            return "en"

        return "hi"

asr_engine = ASREngine()
