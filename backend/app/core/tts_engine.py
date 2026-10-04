import os
import re
import asyncio
from pathlib import Path
from gtts import gTTS

AUDIO_DIR = Path(__file__).parent.parent.parent.parent / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TTSEngine:
    def __init__(self):
        self.lang_map = {
            "mr": "mr",
            "hi": "hi",
            "gu": "gu",
            "en": "en"
        }

    async def synthesize(self, query_id: str, text: str, language: str = "mr") -> str:
        """
        Synthesizes human-like voice audio from advisory text and saves to static/audio.
        Returns the audio endpoint URL for playback and WhatsApp voice message attachment.
        """
        if not text or not text.strip():
            return ""

        filename = f"{query_id}.mp3"
        filepath = AUDIO_DIR / filename

        # If audio already generated, return cached URL
        if filepath.exists() and filepath.stat().st_size > 1000:
            return f"/api/v1/voice/audio/{filename}"

        clean_text = self._clean_for_speech(text)
        if not clean_text:
            clean_text = "नमस्कार! फसलमित्र कृषी सल्ला उपलब्ध आहे."

        target_lang = self.lang_map.get(language, "mr")

        try:
            # Run gTTS in background thread to avoid blocking event loop
            await asyncio.to_thread(self._generate_mp3, clean_text, target_lang, filepath)
            return f"/api/v1/voice/audio/{filename}"
        except Exception as e:
            print(f"[TTSEngine] Error synthesizing speech: {e}", flush=True)
            # Fallback to English if regional voice generation failed
            try:
                if target_lang != "en":
                    await asyncio.to_thread(self._generate_mp3, clean_text, "en", filepath)
                    return f"/api/v1/voice/audio/{filename}"
            except Exception as e2:
                print(f"[TTSEngine] Fallback error: {e2}", flush=True)
            return f"/api/v1/voice/audio/{filename}"

    def _generate_mp3(self, text: str, lang: str, filepath: Path):
        """Thread-safe MP3 generation using gTTS."""
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(filepath))

    def _clean_for_speech(self, text: str) -> str:
        """
        Prepares advisory response for natural, pleasant speech playback:
        - Removes markdown formatting (asterisks, hashtags, bullets, links)
        - Removes emojis
        - Focuses on the core agronomist advice and dosage
        - Caps length for quick, responsive voice note delivery (~40-60 seconds)
        """
        # Remove markdown headers and links
        t = re.sub(r'#{1,6}\s*', '', text)
        t = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', t)
        # Remove bold/italic markers
        t = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', t)
        # Remove bullets, horizontal rules, and decorative symbols
        t = re.sub(r'[-•*~_—]{2,}', ' ', t)
        t = re.sub(r'[-•*]\s*', ' ', t)
        # Remove emojis and non-standard symbols while preserving Devanagari, Gujarati, Latin, numbers, punctuation
        t = re.sub(r'[^\w\s\.,;:!?\u0900-\u097F\u0A80-\u0AFF]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()

        # Voice notes are most effective when concise (first 800 characters or ~120 words)
        if len(t) > 750:
            t = t[:750]
            # Cut cleanly at the last sentence boundary
            last_period = max(t.rfind('.'), t.rfind('।'), t.rfind('?'), t.rfind('!'))
            if last_period > 300:
                t = t[:last_period + 1]

        return t.strip()

tts_engine = TTSEngine()
