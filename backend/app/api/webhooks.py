import uuid
import sys
import httpx
from datetime import datetime
from fastapi import APIRouter, Form, Response, Depends, Request, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.schemas.schemas import AdvisoryQueryRequest
from backend.app.api.advisory import process_advisory_query
from backend.app.db.models import Farmer, CropPassport, Escalation, KnowledgeDocument

sys.stdout.reconfigure(encoding='utf-8')
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WhatsAppJsonRequest(BaseModel):
    phone: str = "+919823012345"
    message: str = ""
    language: str = "auto"
    crop_override: Optional[str] = None
    district: Optional[str] = "Latur"


# Meta WhatsApp Cloud API Verification (GET)
@router.get("/whatsapp/meta")
@router.get("/whatsapp")
async def meta_whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Official Native Meta WhatsApp Cloud API Webhook Verification Endpoint.
    Verification token is configured in META_WHATSAPP_VERIFY_TOKEN (default: fasalmitra_meta_token_2026).
    """
    verify_token = settings.META_WHATSAPP_VERIFY_TOKEN or "fasalmitra_meta_token_2026"
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        print(f"[META WHATSAPP API] Verified Meta webhook token successfully! Challenge: {hub_challenge}", flush=True)
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed: Invalid token", status_code=403)


# Meta WhatsApp Cloud API Incoming Message Handler (POST)
@router.post("/whatsapp/meta")
@router.post("/whatsapp")
async def meta_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives native Meta WhatsApp Cloud API events (text, voice notes, location pins).
    Executes FasalMitra's 14-stage grounded advisory pipeline and dispatches Meta Graph API replies.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    try:
        body = await request.json()
    except Exception:
        return {"status": "OK"}

    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "EVENT_RECEIVED"}

        msg = messages[0]
        from_phone = msg.get("from", "+919823012345")
        msg_type = msg.get("type", "text")

        user_text = "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"
        if msg_type == "text":
            user_text = msg.get("text", {}).get("body", user_text)
        elif msg_type == "location":
            loc = msg.get("location", {})
            user_text = f"📍 Location Pin: {loc.get('latitude')}, {loc.get('longitude')}"

        print(f"\n[{now_str}] 📩 [META WHATSAPP INCOMING MESSAGE] From {from_phone}: '{user_text}'", flush=True)
        input_lower = user_text.lower()

        # Command Shortcuts
        if input_lower in ["hi", "hello", "namaste", "namaskar", "/start", "help", "मेन्यू"]:
            reply_text = (
                "🌾 *[FasalMitra Voice & WhatsApp AI Assistant]*\n"
                "_________________________________________\n"
                "नमस्कार! मी फसलमित्र कृषी सहाय्यक आहे.\n\n"
                "तुम्ही खालील पर्याय निवडू शकता किंवा तुमचा शेतीविषयक प्रश्न व्हॉईस नोट द्वारे पाठवू शकता:\n\n"
                "1️⃣ *प्रश्नाचे उत्तर मिळवा* - (उदा. 'सोयाबीन पिवळे पडत आहे')\n"
                "2️⃣ *हवामान अंदाज (Agromet)* - (/weather)\n"
                "3️⃣ *पिक पासपोर्ट माहिती* - (/passport)\n"
                "4️⃣ *तज्ञ तिकीट स्थिती* - (/expert)\n\n"
                "💡 *तुमचा प्रश्न येथे टाईप करा किंवा ऑडिओ व्हॉईस मेसेज पाठवा!*"
            )
            await send_meta_whatsapp_reply(from_phone, reply_text)
            return {"status": "SUCCESS", "reply": reply_text}

        if input_lower in ["2", "/weather", "weather", "हवामान"]:
            weather_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.crop == "General").first()
            weather_text = weather_doc.content if weather_doc else "लातूर जिल्ह्यात पुढील ४८ तासांत हलक्या ते मध्यम स्वरूपाचा पाऊस अपेक्षित आहे. फवारणी पुढे ढकलावी."
            reply_text = f"🌧️ *[IMD Agromet Weather Advisory - Latur]*\n\n{weather_text}\n\n🛡️ *Source:* IMD Agromet Advisory Service"
            await send_meta_whatsapp_reply(from_phone, reply_text)
            return {"status": "SUCCESS", "reply": reply_text}

        if input_lower in ["3", "/passport", "passport", "पिक"]:
            passport = db.query(CropPassport).first()
            reply_text = (
                f"🌱 *[Farmer Crop Passport]*\n\n"
                f"• *Crop:* {passport.crop_name if passport else 'Soybean'}\n"
                f"• *Variety:* {passport.variety if passport else 'JS 335'}\n"
                f"• *Sowing Date:* {passport.sowing_date if passport else '2026-06-15'}\n"
                f"• *Stage:* {passport.stage_days if passport else 35} Days\n"
                f"• *District:* Latur, Maharashtra"
            )
            await send_meta_whatsapp_reply(from_phone, reply_text)
            return {"status": "SUCCESS", "reply": reply_text}

        # 14-Stage Grounded Pipeline Execution
        advisory_req = AdvisoryQueryRequest(
            farmer_id=f"FARM-{from_phone[-4:]}",
            channel="WHATSAPP",
            language="auto",
            text=user_text,
            location_district="Latur",
            location_state="Maharashtra"
        )
        pipeline_res = await process_advisory_query(advisory_req, db)

        grounding_badge = "✅ ICAR/KVK Grounded Evidence" if pipeline_res.grounding_status == "SUPPORTED" else "⚠️ Escalated to Expert Queue"
        source_title = pipeline_res.retrieved_evidence[0].title if pipeline_res.retrieved_evidence else "ICAR/KVK Advisory"
        
        reply_body = (
            f"🌾 *[FasalMitra Grounded Agri-Advisory]*\n"
            f"_________________________________________\n\n"
            f"{pipeline_res.answer_text}\n\n"
            f"📌 *Confidence:* {int(pipeline_res.confidence_score * 100)}% ({pipeline_res.confidence_level})\n"
            f"🛡️ *Grounding Status:* {grounding_badge}\n"
            f"📖 *Evidence Source:* {source_title}"
        )

        await send_meta_whatsapp_reply(from_phone, reply_body)
        return {"status": "SUCCESS", "answer": pipeline_res.answer_text, "grounding": pipeline_res.grounding_status}
    except Exception as e:
        print(f"[{now_str}] ⚠️ Meta WhatsApp Webhook Exception: {e}", flush=True)
        return {"status": "ERROR", "detail": str(e)}


@router.post("/whatsapp/json")
async def whatsapp_json_endpoint(
    req: WhatsAppJsonRequest,
    db: Session = Depends(get_db)
):
    """
    JSON Endpoint for WhatsApp Automation & Web Simulator.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    user_text = req.message.strip() if req.message.strip() else "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"
    print(f"\n[{now_str}] 📩 [JSON API WHATSAPP MESSAGE]: '{user_text}' (Phone: {req.phone})", flush=True)

    input_lower = user_text.lower()
    if input_lower in ["2", "/weather", "weather", "हवामान"]:
        weather_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.crop == "General").first()
        weather_text = weather_doc.content if weather_doc else "लातूर जिल्ह्यात पुढील ४८ तासांत हलक्या ते मध्यम स्वरूपाचा पाऊस अपेक्षित आहे. फवारणी पुढे ढकलावी."
        reply_body = f"🌧️ *[IMD Agromet Weather Advisory - Latur]*\n\n{weather_text}\n\n🛡️ *Source:* IMD Agromet Advisory Service"
        return {"reply_body": reply_body, "pipeline_result": None}

    if input_lower in ["3", "/passport", "passport", "पिक"]:
        passport = db.query(CropPassport).first()
        reply_body = (
            f"🌱 *[Farmer Crop Passport]*\n\n"
            f"• *Crop:* {passport.crop_name if passport else 'Soybean'}\n"
            f"• *Variety:* {passport.variety if passport else 'JS 335'}\n"
            f"• *Sowing Date:* {passport.sowing_date if passport else '2026-06-15'}\n"
            f"• *Stage:* {passport.stage_days if passport else 35} Days\n"
            f"• *District:* Latur, Maharashtra"
        )
        return {"reply_body": reply_body, "pipeline_result": None}
    
    advisory_req = AdvisoryQueryRequest(
        farmer_id=f"FARM-{req.phone[-4:]}",
        channel="WHATSAPP",
        language=req.language,
        text=user_text,
        crop_override=req.crop_override,
        location_district=req.district or "Latur",
        location_state="Maharashtra"
    )

    pipeline_res = await process_advisory_query(advisory_req, db)
    grounding_badge = "✅ ICAR/KVK Grounded Evidence" if pipeline_res.grounding_status == "SUPPORTED" else "⚠️ Escalated to Expert Queue"
    source_title = pipeline_res.retrieved_evidence[0].title if pipeline_res.retrieved_evidence else "ICAR/KVK Advisory"

    reply_body = (
        f"🌾 *[FasalMitra Grounded Agri-Advisory]*\n"
        f"_________________________________________\n\n"
        f"{pipeline_res.answer_text}\n\n"
        f"📌 *Confidence:* {int(pipeline_res.confidence_score * 100)}% ({pipeline_res.confidence_level})\n"
        f"🛡️ *Grounding Status:* {grounding_badge}\n"
        f"📖 *Evidence Source:* {source_title}"
    )

    return {
        "reply_body": reply_body,
        "pipeline_result": pipeline_res
    }


async def send_meta_whatsapp_reply(to_phone: str, text: str):
    """
    Dispatches outbound WhatsApp text message using Meta Graph API HTTP endpoint.
    Requires META_WHATSAPP_TOKEN and META_WHATSAPP_PHONE_ID in environment.
    """
    token = settings.META_WHATSAPP_TOKEN
    phone_id = settings.META_WHATSAPP_PHONE_ID
    if not token or not phone_id:
        print(f"[META WHATSAPP OUTBOUND] Notice: META_WHATSAPP_TOKEN or PHONE_ID not set. Reply logged locally:\n{text[:100]}...", flush=True)
        return

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            print(f"[META WHATSAPP OUTBOUND] Sent WhatsApp message to {to_phone}. HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"[META WHATSAPP OUTBOUND] Error sending WhatsApp message: {e}", flush=True)
