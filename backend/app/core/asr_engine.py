import re
from typing import Tuple

class ASREngine:
    def __init__(self):
        # Language keywords detection matrix
        self.marathi_keywords = ["माझ्या", "पाने", "पडत", "आहेत", "काय", "करू", "झाली", "पिक", "शेतकरी", "भाऊ", "कीड", "फवारणी"]
        self.hindi_keywords = ["मेरा", "मेरे", "पत्ते", "पीले", "क्या", "करें", "दवा", "डालें", "फसल", "इल्ली", "कीड़ा", "उपयोग", "कौन", "कौनसी", "स्प्रे"]
        self.gujarati_keywords = ["મારા", "પાંદડા", "પીળા", "સોયાબીન", "શું", "કરવું", "પાક"]

    async def transcribe(self, text_input: str, audio_base64: str = None, requested_lang: str = "auto") -> Tuple[str, str, float]:
        """
        Returns: (normalized_transcript, detected_language, confidence_score)
        """
        transcript = text_input.strip() if text_input else "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"
        
        # Language detection logic
        detected_lang = requested_lang
        if requested_lang == "auto" or not requested_lang:
            detected_lang = self._detect_language(transcript)

        # Transcript normalization (remove filler words)
        normalized = re.sub(r'\b(uh|um|मतलब|म्हणजे|अरे)\b', '', transcript, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        confidence = 0.95 if audio_base64 is None else 0.88
        return normalized, detected_lang, confidence

    def _detect_language(self, text: str) -> str:
        # Check Gujarati Unicode script range (\u0A80-\u0AFF)
        if any('\u0a80' <= c <= '\u0aff' for c in text):
            return "gu"

        for kw in self.hindi_keywords:
            if kw in text:
                return "hi"
        for kw in self.marathi_keywords:
            if kw in text:
                return "mr"
        
        if text.isascii():
            return "en"

        return "mr" if "आहे" in text or "माझ्या" in text else "hi"

asr_engine = ASREngine()
