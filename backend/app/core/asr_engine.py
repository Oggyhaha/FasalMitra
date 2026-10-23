import os
import re
import httpx
from typing import Tuple, Optional
from backend.app.config import settings

class ASREngine:
    def __init__(self):
        # Language keywords detection matrix for native scripts
        self.marathi_keywords = [
            "माझ्या", "पाने", "पडत", "आहेत", "आहे", "काय", "करू", "झाली", "झाला", "पिक",
            "शेतकरी", "भाऊ", "कीड", "फवारणी", "लक्षणे", "शेती", "सांगा", "पिवळे", "उपाय", "कसा"
        ]
        self.hindi_keywords = [
            "मेरा", "मेरे", "मेरी", "पत्ते", "पीले", "क्या", "करें", "करूं", "दवा", "डालें",
            "फसल", "इल्ली", "कीड़ा", "कीड़े", "उपयोग", "कौन", "कौनसी", "स्प्रे", "रोग", "इलाज",
            "बताएं", "बताओ", "चाहिए", "पेड़", "पौधा", "पौधे", "होता", "होती", "होते"
        ]
        self.gujarati_keywords = [
            "મારા", "પાંદડા", "પીળા", "સોયાબીન", "શું", "કરવું", "પાક", "બટાકા", "ખેતી",
            "કિડા", "બાજરી", "કપાસ", "છંટકાવ", "ખાતર", "છે", "નથી", "વેલ", "ઝાડ", "વાવણી"
        ]

        # Romanized Gujarati Lexicon (Distinctive Gujlish markers)
        self.gujarati_roman_words = {
            # Auxiliaries, copulas, and verb tenses
            "che", "chhe", "chho", "cho", "nathi", "thase", "thashe", "thay", "thaye", "thaine", "thava",
            "karvu", "karvi", "karvo", "karvanu", "karvani", "karvano", "karyu", "karie", "avshe", "aavshe",
            "aave", "aavyu", "joyiye", "joie", "joiye", "joye", "lidhe", "lidho", "lidha", "rahyu", "rahya",
            # Pronouns & determiners
            "mare", "maro", "mari", "maru", "mara", "tamare", "tamaro", "tamari", "tamaru", "tamara",
            "amare", "amaro", "amari", "amaru", "amara", "aamne", "tamne", "mane", "tene", "jeno", "jeni", "jenu",
            # Question words & prepositions
            "kemni", "kemne", "kem", "su", "shu", "syu", "kyare", "kyaare", "kyathi",
            "ketlu", "ketla", "ketli", "kai", "kayi", "kayo", "kayu", "kevi", "kevo", "kevu",
            "kaho", "janavo", "batavo", "mate", "aapo",
            # Agricultural vocabulary & common Gujarati nouns
            "bajari", "bajri", "bataka", "batata", "bataaka", "batako", "kapas", "kapaas",
            "ghau", "ghaun", "eranda", "diwela", "raydo", "jeeru", "jira", "magfali", "sing",
            "khedut", "kheduto", "khetar", "vavetar", "vavni", "chhatkav", "chhantkav", "chhatvi", "chhatvu",
            "khatar", "jiwat", "jeewat", "eeyal", "iyal", "paak", "pandada", "paandada",
            "sukay", "sukaay", "bhaav", "vadhare", "vadhu", "thodu", "saru", "haji", "haju", "kheti"
        }

        self.gujarati_roman_phrases = [
            "karvi che", "karvu che", "karvo che", "padi che", "thay che", "aave che",
            "kem cho", "kem chho", "su karvu", "shu karvu", "kemni thase", "kem thase",
            "bataka ma", "kapas ma", "khetar ma", "pak ma", "paak ma", "dava chhatvi",
            "mate su", "che kemni", "karvi chhe", "karvu chhe", "aapo idea", "idea aapo"
        ]

        # Romanized Marathi Lexicon (Marathlish)
        self.marathi_roman_words = {
            "ahe", "aahe", "nahit", "hota", "hoti", "hote", "mala", "tula", "tyala", "amha",
            "maza", "mazya", "mazi", "amche", "tumche", "kasa", "kashi", "kase", "kiti",
            "kay", "kaay", "kadhi", "kuthe", "karaycha", "karaychi", "karu", "sangaa", "sanga",
            "sangu", "vikni", "sheti", "bhau", "pika", "panne", "fawarani", "fawarni", "sakto", "apan"
        }

        self.marathi_roman_phrases = [
            "ahe ka", "aahe ka", "kay karu", "kaay karu", "kasa karu", "kashi karu",
            "sheti karaychi", "vikni karna", "vikni karaychi", "upay sanga", "upay sangaa"
        ]

        # Romanized Hindi Lexicon (Comprehensive Hinglish)
        self.hindi_roman_words = {
            # Auxiliaries, copulas, and verb tenses
            "hai", "hain", "ho", "hu", "hoon", "hoga", "hogi", "hoge", "tha", "thi",
            # Prepositions & Postpositions
            "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "tak", "liye", "bhi",
            # Question words & Verbs
            "kya", "kaise", "karen", "kare", "karna", "karo", "karta", "karti", "karte", "kiya",
            # Pronouns
            "mera", "mere", "meri", "humara", "hamara", "hum", "mujhe", "apna", "apne", "apni",
            "aap", "aapka", "aapke", "aapki", "tum", "tumhara", "tumhare", "kisko", "kisse",
            # Botanical & Agricultural terms
            "paudha", "paudhe", "ped", "jhad", "fasal", "khet", "kheti", "kisan", "kisano",
            "dawa", "dawai", "chhidkav", "rog", "keeda", "keede", "keedo", "bimari", "patte", "patti",
            "lagaye", "lagana", "lagayein", "lagate", "lagaya", "lagti", "lagta", "ugaye", "ugana", "ugayein",
            # Modals & Adverbs
            "bataiye", "batao", "bataye", "batayein", "chahiye", "sakte", "sakta", "sakti", "raha", "rahe", "rahi",
            "nahi", "nahin", "mat", "agar", "lekin", "aur", "ya", "jaise", "konsi", "kaunsi", "kitna", "kitni", "kab", "kyun", "kyu"
        }

        self.hindi_roman_phrases = [
            "kaise kare", "kya kare", "kya karna", "kaise lagaye", "kaise ugaye",
            "kaise hoga", "kab dale", "kab karna", "konsi dawai", "konsi dawa",
            "kaunsi dawai", "kaunsi dawa", "keeda laga", "rog laga", "patte pile",
            "kisan bhai", "hum kaise", "ped kaise", "paudha kaise", "khet me",
            "spray kab", "dawa kab", "batao bhai", "bataiye na", "kya hum",
            "ho raha hai", "ho rahi hai", "ho rahe hai", "lag raha hai", "kare kya",
            "idea dijiye", "idea do", "tarbuj ka", "tarbooz ka", "watermelon ka"
        ]

        # Standard English Grammatical & Functional Words
        self.english_grammar_words = {
            "how", "to", "what", "is", "the", "why", "are", "which", "should", "i", "can", "for",
            "please", "tell", "when", "about", "with", "from", "this", "that", "do", "does", "did",
            "will", "would", "shall", "could", "there", "where", "process", "grow", "recommend",
            "suggest", "explain", "guide", "steps", "management", "control"
        }

    async def transcribe(self, text_input: str, audio_base64: str = None, requested_lang: str = "auto") -> Tuple[str, str, float]:
        """
        Transcribes speech audio or normalizes text input.
        Returns: (normalized_transcript, detected_language, confidence_score)
        """
        transcript = text_input.strip() if text_input else ""
        audio_lang = None

        # If audio voice message is provided, transcribe and detect language directly via Gemini
        if audio_base64 and audio_base64.strip():
            audio_text, audio_lang = await self._transcribe_audio_with_gemini(audio_base64)
            if audio_text:
                transcript = audio_text

        if not transcript:
            transcript = "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"

        # Language detection priority:
        # 1. Explicitly requested language from caller (if not 'auto')
        # 2. Directly acoustically recognized language from voice note audio
        # 3. Robust multilingual script and transliterated n-gram classifier
        detected_lang = requested_lang
        if requested_lang == "auto" or not requested_lang:
            text_lang = self._detect_language(transcript)
            # If native script text has dominant non-Latin characters, text_lang is ground truth
            has_indic_script = any(
                sum(1 for c in transcript if s_start <= c <= s_end) >= 2
                for s_start, s_end in [
                    ('\u0a80', '\u0aff'), # gu
                    ('\u0900', '\u097f'), # dev
                    ('\u0a00', '\u0a7f'), # pa
                    ('\u0980', '\u09ff'), # bn
                    ('\u0c00', '\u0c7f'), # te
                    ('\u0b80', '\u0bff'), # ta
                    ('\u0c80', '\u0cff'), # kn
                    ('\u0d00', '\u0d7f'), # ml
                    ('\u0b00', '\u0b7f'), # or
                    ('\u0600', '\u06ff'), # ur
                ]
            )
            if has_indic_script:
                detected_lang = text_lang
            elif audio_lang:
                detected_lang = audio_lang
            else:
                detected_lang = text_lang

        # Transcript normalization (remove conversational filler words)
        normalized = re.sub(r'\b(uh|um|मतलब|म्हणजे|અરે|अच्छा|हां)\b', '', transcript, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        confidence = 0.95 if audio_base64 is None else 0.92
        return normalized, detected_lang, confidence

    async def _transcribe_audio_with_gemini(self, audio_base64: str, mime_type: str = "audio/ogg") -> Tuple[str, Optional[str]]:
        """
        Transcribes regional Indian farmer voice notes using Gemini Flash Multimodal Audio.
        Returns: (transcribed_text, detected_language_code)
        """
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return "", None

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
                                "You are an expert speech recognition and language identification system for Indian farmers. "
                                "Accurately identify the exact spoken regional Indian language (hi, gu, mr, pa, bn, te, ta, kn, ml, or, ur, en). "
                                "IMPORTANT: Marathi uses Devanagari script (e.g. शेतकरी, पिक, माहिती, सोयाबीन, कापूस, फवारणी, आहे). "
                                "Do not confuse Marathi with Bengali or Assamese. "
                                "Gujarati uses Gujarati script (ખેડૂત, પાક, છે). "
                                "Hindi uses Devanagari script (किसान, फसल, है). "
                                "Strict output format:\n"
                                "LANGUAGE: <code>\n"
                                "TRANSCRIPT: <text>"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 400
            }
        }

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        safe_log = raw_text.encode('ascii', errors='replace').decode('ascii')
                        print(f"[ASREngine] Gemini Raw Speech Output:\n{safe_log}", flush=True)

                        detected_lang = None
                        transcript_text = raw_text

                        for line in raw_text.splitlines():
                            line_s = line.strip()
                            if line_s.upper().startswith("LANGUAGE:"):
                                code = line_s.split(":", 1)[1].strip().lower()
                                if code in [
                                    "hi", "gu", "mr", "pa", "en", "bn", "te", "ta", "kn",
                                    "ml", "or", "ur", "as", "sa", "ne", "kok", "mai", "doi", "ks", "sd"
                                ]:
                                    detected_lang = code
                            elif line_s.upper().startswith("TRANSCRIPT:"):
                                transcript_text = line_s.split(":", 1)[1].strip()

                        return transcript_text, detected_lang
                else:
                    print(f"[ASREngine] Gemini Audio API HTTP {res.status_code}: {res.text[:100]}", flush=True)
        except Exception as e:
            print(f"[ASREngine] Gemini Audio Transcription error: {e}", flush=True)

        return "", None

    def _detect_language(self, text: str) -> str:
        # 1. Native Script Majority Classification for all 22 Scheduled Indian Languages + English
        script_counts = {
            "gu": sum(1 for c in text if '\u0a80' <= c <= '\u0aff'),
            "pa": sum(1 for c in text if '\u0a00' <= c <= '\u0a7f'),
            "te": sum(1 for c in text if '\u0c00' <= c <= '\u0c7f'),
            "ta": sum(1 for c in text if '\u0b80' <= c <= '\u0bff'),
            "kn": sum(1 for c in text if '\u0c80' <= c <= '\u0cff'),
            "ml": sum(1 for c in text if '\u0d00' <= c <= '\u0d7f'),
            "or": sum(1 for c in text if '\u0b00' <= c <= '\u0b7f'),
            "ur": sum(1 for c in text if '\u0600' <= c <= '\u06ff'),
            "sat": sum(1 for c in text if '\u1c50' <= c <= '\u1c7f'),
            "mni": sum(1 for c in text if '\uabc0' <= c <= '\uabff'),
            "bn_as": sum(1 for c in text if '\u0980' <= c <= '\u09ff'),
            "dev": sum(1 for c in text if '\u0900' <= c <= '\u097f'),
        }
        max_script_count = max(script_counts.values()) if script_counts else 0

        if max_script_count >= 2:
            top_script = [k for k, v in script_counts.items() if v == max_script_count][0]
            if top_script == "gu":
                return "gu"
            if top_script == "pa":
                return "pa"
            if top_script == "te":
                return "te"
            if top_script == "ta":
                return "ta"
            if top_script == "kn":
                return "kn"
            if top_script == "ml":
                return "ml"
            if top_script == "or":
                return "or"
            if top_script == "ur":
                return "ur"
            if top_script == "sat":
                return "sat"
            if top_script == "mni":
                return "mni"
            if top_script == "bn_as":
                return "as" if any(c in text for c in ['\u09f0', '\u09f1']) else "bn"
            if top_script == "dev":
                # Check regional dialect markers
                if any(w in text for w in ["अस्ति", "कृषिः", "भवति", "नमः"]):
                    return "sa" # Sanskrit
                if any(w in text for w in ["छ", "छन्", "भयो", "गर्ने", "हाम्रो"]):
                    return "ne" # Nepali
                if any(w in text for w in ["आसा", "आसात", "करचे", "भास"]):
                    return "kok" # Konkani
                if any(w in text for w in ["अछि", "छथि", "हमर", "करब"]):
                    return "mai" # Maithili

                # Distinguish Marathi vs Hindi in Devanagari
                mr_count = sum(1 for kw in self.marathi_keywords if kw in text)
                hi_count = sum(1 for kw in self.hindi_keywords if kw in text)

                if any(w in text for w in ["आहे", "आहेत", "माझ्या", "शेती", "पिकावर", "करावे", "सांगा", "शेतकरी", "पिक", "पेरणी", "पिवळे", "झाली"]):
                    return "mr"
                if mr_count > hi_count:
                    return "mr"
                if hi_count > mr_count:
                    return "hi"
                return "hi"

        # 3. Transliterated / Romanized Script Recognition (English alphabet used for Indian languages)
        text_clean = text.lower()
        words = set(re.findall(r'\b[a-z]+\b', text_clean))

        # Check Romanized Gujarati (Gujlish)
        gu_score = len(words.intersection(self.gujarati_roman_words))
        for phrase in self.gujarati_roman_phrases:
            if phrase in text_clean:
                gu_score += 4

        # Check Romanized Marathi (Marathlish)
        mr_score = len(words.intersection(self.marathi_roman_words))
        for phrase in self.marathi_roman_phrases:
            if phrase in text_clean:
                mr_score += 4

        # Check Romanized Hindi (Hinglish)
        hi_score = len(words.intersection(self.hindi_roman_words))
        for phrase in self.hindi_roman_phrases:
            if phrase in text_clean:
                hi_score += 4

        # Check Standard English Grammar
        en_score = len(words.intersection(self.english_grammar_words))

        # Decision rules:
        # 1. Pure English dominates if multiple grammatical English words appear and exceed Indic tokens
        if en_score >= 2 and en_score > max(hi_score, gu_score, mr_score):
            return "en"

        # 2. Distinctive Gujlish wins if Gujarati markers are strongest
        if gu_score > 0 and gu_score > max(hi_score, mr_score):
            return "gu"

        # 3. Distinctive Marathlish wins if Marathi markers are strongest
        if mr_score > 0 and mr_score > max(hi_score, gu_score):
            return "mr"

        # 4. Hinglish wins if Hindi markers are detected
        if hi_score > 0:
            return "hi"

        # 5. Fallback for short single-word / standard ASCII text
        if en_score > 0:
            return "en"

        if text.isascii():
            return "en"

        return "hi"

asr_engine = ASREngine()
