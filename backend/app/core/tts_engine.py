class TTSEngine:
    async def synthesize(self, query_id: str, text: str, language: str) -> str:
        """
        Synthesizes TTS audio URL. Returns endpoint URL for client audio playback.
        """
        return f"/api/v1/voice/audio/{query_id}.mp3"

tts_engine = TTSEngine()
