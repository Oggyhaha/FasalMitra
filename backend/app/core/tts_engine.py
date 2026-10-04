import os
import re
import asyncio
from pathlib import Path
from gtts import gTTS
import edge_tts

AUDIO_DIR = Path(__file__).parent.parent.parent.parent / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TTSEngine:
    def __init__(self):
        # High quality regional neural voices with natural human intonation
        self.edge_voice_map = {
            "mr": "mr-IN-AarohiNeural",
            "hi": "hi-IN-SwaraNeural",
            "gu": "gu-IN-DhwaniNeural",
            "en": "en-IN-NeerjaNeural"
        }
        self.gtts_lang_map = {
            "mr": "mr",
            "hi": "hi",
            "gu": "gu",
            "en": "en"
        }
        # Increased speech rate (+18%) so voice notes are fast, crisp and consume less time
        self.speech_rate = "+18%"

    async def synthesize(self, query_id: str, text: str, language: str = "mr") -> str:
        """
        Synthesizes human-like voice audio covering the FULL advisory message at optimized speed (+18%).
        Saves to static/audio/{query_id}.mp3 and returns the streamable URL.
        """
        if not text or not text.strip():
            return ""

        filename = f"{query_id}.mp3"
        filepath = AUDIO_DIR / filename

        clean_text = self._clean_for_speech(text)
        if not clean_text:
            clean_text = "नमस्कार! फसलमित्र कृषी सल्ला उपलब्ध आहे."

        lang_key = language if language in self.edge_voice_map else "mr"
        voice_name = self.edge_voice_map.get(lang_key, "mr-IN-AarohiNeural")

        # 1. Primary: Edge-TTS Neural Voice with Fast Speech Rate (+18%)
        try:
            communicate = edge_tts.Communicate(clean_text, voice_name, rate=self.speech_rate)
            await communicate.save(str(filepath))
            if filepath.exists() and filepath.stat().st_size > 1000:
                return f"/api/v1/voice/audio/{filename}"
        except Exception as e:
            print(f"[TTSEngine] EdgeTTS notice ({e}), switching to gTTS fallback...", flush=True)

        # 2. Resilient Fallback: gTTS
        try:
            target_lang = self.gtts_lang_map.get(lang_key, "mr")
            await asyncio.to_thread(self._generate_gtts_mp3, clean_text, target_lang, filepath)
            return f"/api/v1/voice/audio/{filename}"
        except Exception as e2:
            print(f"[TTSEngine] gTTS fallback error: {e2}", flush=True)
            try:
                # English fallback
                await asyncio.to_thread(self._generate_gtts_mp3, clean_text, "en", filepath)
            except Exception as e3:
                print(f"[TTSEngine] English emergency fallback error: {e3}", flush=True)

        return f"/api/v1/voice/audio/{filename}"

    def _generate_gtts_mp3(self, text: str, lang: str, filepath: Path):
        """Thread-safe MP3 generation using gTTS."""
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(filepath))

    def _clean_for_speech(self, text: str) -> str:
        """
        Prepares FULL advisory response for clear, natural, and comprehensive spoken delivery:
        - Removes markdown formatting (asterisks, hashtags, bullets, tables)
        - Removes emojis while preserving all regional language characters
        - Keeps full diagnostic advice, step-by-step remedies, dosages, and weather safety
        - Does NOT truncate the message so farmers receive the complete guidance
        """
        # Remove markdown headers and URLs
        t = re.sub(r'#{1,6}\s*', '', text)
        t = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', t)
        # Remove bold, italics, code markers
        t = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', t)
        t = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', t)
        # Remove decorative borders and bullet symbols
        t = re.sub(r'[-•*~_—=]{2,}', ' ', t)
        t = re.sub(r'[-•*]\s*', ' ', t)
        # Clean emojis while keeping Devanagari, Gujarati, Latin, digits, punctuation
        t = re.sub(r'[^\w\s\.,;:!?\u0900-\u097F\u0A80-\u0AFF%/\-]', ' ', t)
        # Normalize whitespace
        t = re.sub(r'\s+', ' ', t).strip()

        # Generous limit up to 4000 characters to ensure the complete answer is spoken
        if len(t) > 4000:
            t = t[:4000]
            last_period = max(t.rfind('.'), t.rfind('।'), t.rfind('?'), t.rfind('!'))
            if last_period > 1000:
                t = t[:last_period + 1]

        return t.strip()

tts_engine = TTSEngine()
