import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.app.core.tts_engine import tts_engine, AUDIO_DIR

router = APIRouter(prefix="/voice", tags=["voice"])

class SynthesizeVoiceRequest(BaseModel):
    query_id: str = "custom_voice"
    text: str
    language: str = "mr"

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Streams voice note MP3 audio file for browser playback and WhatsApp attachments.
    """
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400"
        }
    )

@router.post("/synthesize")
async def synthesize_voice_on_demand(req: SynthesizeVoiceRequest):
    """
    Synthesizes custom voice note on-demand and returns the playback URL.
    """
    audio_url = await tts_engine.synthesize(req.query_id, req.text, req.language)
    return {"audio_url": audio_url}
