import uuid
import sys
import httpx
from datetime import datetime
from fastapi import APIRouter, Form, Response, Depends, Request, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
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

@router.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(default="whatsapp:+919823012345"),
    Body: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
    Latitude: Optional[str] = Form(None),
    Longitude: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Live WhatsApp AI Assistant Webhook Endpoint (Twilio WhatsApp Sandbox & Meta Cloud API)
    Receives voice note audio, location pins, or text messages from farmer and executes 14-stage grounded advisory pipeline.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    farmer_phone = From.replace("whatsapp:", "")
    raw_input = Body.strip() if Body else ""
    input_lower = raw_input.lower()

    print(f"\n[{now_str}] 📩 [WEBHOOK INCOMING WHATSAPP MESSAGE] From {farmer_phone}: '{raw_input}'", flush=True)

    # 1. Location Pin Handling
    district = "Latur"
    if Latitude and Longitude:
        reply = (
            f"📍 *[Location Received]*\n"
            f"Coordinates: {Latitude}, {Longitude}\n"
            f"District: Latur, Maharashtra\n\n"
            f"तुमच्या परिसरातील हवामान अंदाज आणि कृषी सल्ला अपडेट केला आहे."
        )
        print(f"[{now_str}] 📍 Processed Location Pin: {Latitude}, {Longitude}", flush=True)
        return format_twiml_response(reply)

    # 2. Interactive Menu / Command Shortcuts
    if input_lower in ["hi", "hello", "namaste", "namaskar", "/start", "help", "मेन्यू"]:
        welcome_msg = (
            "🌾 *[FasalMitra Voice & WhatsApp AI Assistant]*\n"
            "_________________________________________\n"
            "नमस्कार! मी फसलमित्र कृषी सहाय्यक आहे.\n\n"
            "तुम्ही खालील पर्याय निवडू शकता किंवा तुमचा शेतीविषयक प्रश्न व्हॉईस नोट द्वारे पाठवू शकता:\n\n"
            "1️⃣ *प्रश्नाचे उत्तर मिळवा* - (उदा. 'सोयाबीन पिवळे पडत आहे')\n"
            "2️⃣ *हवामान अंदाज (Agromet)* - (/weather)\n"
            "3️⃣ *पिक पासपोर्ट माहिती* - (/passport)\n"
            "4️⃣ *तज्ञ तिकीट स्थिती* - (/expert)\n"
            "5️⃣ *भाषा बदला (Language)* - (/lang mr/hi/en/gu)\n\n"
            "💡 *तुमचा प्रश्न येथे टाईप करा किंवा ऑडिओ व्हॉईस मेसेज पाठवा!*"
        )
        print(f"[{now_str}] 🤖 Sent Welcome Menu to {farmer_phone}", flush=True)
        return format_twiml_response(welcome_msg)

    if input_lower in ["2", "/weather", "weather", "हवामान"]:
        weather_doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.crop == "General").first()
        weather_text = weather_doc.content if weather_doc else "लातूर जिल्ह्यात पुढील ४८ तासांत हलक्या ते मध्यम स्वरूपाचा पाऊस अपेक्षित आहे. फवारणी पुढे ढकलावी."
        reply = f"🌧️ *[IMD Agromet Weather Advisory - Latur]*\n\n{weather_text}\n\n🛡️ *Source:* IMD Agromet Advisory Service"
        print(f"[{now_str}] 🌧️ Sent Weather Bulletin to {farmer_phone}", flush=True)
        return format_twiml_response(reply)

    if input_lower in ["3", "/passport", "passport", "पिक"]:
        passport = db.query(CropPassport).first()
        if passport:
            reply = (
                f"🌱 *[Farmer Crop Passport]*\n\n"
                f"• *Crop:* {passport.crop_name}\n"
                f"• *Variety:* {passport.variety}\n"
                f"• *Sowing Date:* {passport.sowing_date}\n"
                f"• *Stage:* {passport.stage_days} Days ({passport.season})\n"
                f"• *District:* Latur, Maharashtra"
            )
        else:
            reply = "🌱 *[Crop Passport]*: Soybean JS 335 (35 Days - Flowering stage)."
        print(f"[{now_str}] 📜 Sent Crop Passport to {farmer_phone}", flush=True)
        return format_twiml_response(reply)

    if input_lower in ["4", "/expert", "expert", "तज्ञ"]:
        escalation = db.query(Escalation).order_by(Escalation.created_at.desc()).first()
        if escalation:
            status_emoji = "⏳" if escalation.status == "OPEN" else "✅"
            reply = (
                f"👨‍🌾 *[Expert Escalation Status]*\n\n"
                f"• *Ticket ID:* {escalation.id}\n"
                f"• *Status:* {status_emoji} {escalation.status}\n"
                f"• *Reason:* {escalation.reason}\n"
                f"• *Expert Answer:* {escalation.expert_answer or 'तज्ञांची पडताळणी सुरू आहे.'}"
            )
        else:
            reply = "ℹ️ तुमच्या नावावर सध्या कोणतेही प्रलंबित तज्ञ तिकीट नाही."
        print(f"[{now_str}] 👨‍🌾 Sent Expert Ticket Status to {farmer_phone}", flush=True)
        return format_twiml_response(reply)

    # 3. Execute Advisory Pipeline for Farmer Voice or Text Question
    user_text = raw_input if raw_input else "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"

    advisory_req = AdvisoryQueryRequest(
        farmer_id=f"FARM-{farmer_phone[-4:]}",
        channel="WHATSAPP",
        language="auto",
        text=user_text,
        location_district=district,
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

    print(f"[{now_str}] 🚀 Generated Pipeline Reply for {farmer_phone} (Confidence: {pipeline_res.confidence_score}):\n{reply_body[:120]}...\n", flush=True)
    return format_twiml_response(reply_body, pipeline_res.audio_url)


# Meta WhatsApp Cloud API Verification (GET)
@router.get("/whatsapp/meta")
async def meta_whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Meta WhatsApp Cloud API Webhook Verification.
    """
    VERIFY_TOKEN = "fasalmitra_meta_token_2026"
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("[META API WEBHOOK] Verified Meta token successfully!", flush=True)
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


# Meta WhatsApp Cloud API Message Receiver (POST)
@router.post("/whatsapp/meta")
async def meta_whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives native Meta WhatsApp Cloud API JSON events.
    """
    body = await request.json()
    now_str = datetime.now().strftime("%H:%M:%S")
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

        text_content = "माझ्या सोयाबीनची पाने पिवळी पडत आहेत"
        if msg_type == "text":
            text_content = msg.get("text", {}).get("body", text_content)

        print(f"[{now_str}] 📩 [META WHATSAPP EVENT] From {from_phone}: '{text_content}'", flush=True)

        advisory_req = AdvisoryQueryRequest(
            farmer_id=f"FARM-{from_phone[-4:]}",
            channel="WHATSAPP",
            language="auto",
            text=text_content,
            location_district="Latur",
            location_state="Maharashtra"
        )
        pipeline_res = await process_advisory_query(advisory_req, db)
        return {"status": "SUCCESS", "answer": pipeline_res.answer_text, "grounding": pipeline_res.grounding_status}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}


@router.post("/whatsapp/json")
async def whatsapp_json_endpoint(
    req: WhatsAppJsonRequest,
    db: Session = Depends(get_db)
):
    """
    JSON API Endpoint for WhatsApp Automation & Web Simulator.
    Returns JSON response payload with structured grounding metrics.
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

    print(f"[{now_str}] 🚀 Returned Grounded Answer (Confidence {pipeline_res.confidence_score}):\n{reply_body[:120]}...\n", flush=True)

    return {
        "reply_body": reply_body,
        "pipeline_result": pipeline_res
    }


def format_twiml_response(body_text: str, audio_url: Optional[str] = None):
    media_xml = f"<Media>{audio_url}</Media>" if audio_url else ""
    response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>{body_text}</Body>
        {media_xml}
    </Message>
</Response>"""
    return Response(content=response_xml, media_type="application/xml")


@router.post("/phone")
async def phone_ivr_webhook(
    Caller: str = Form(default="+919823012345"),
    SpeechResult: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Live Phone IVR Gateway Webhook Endpoint
    Handles voice call interaction directly over ordinary phone call.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{now_str}] 📞 [PHONE IVR CALL] Caller: {Caller}, Speech: '{SpeechResult}'", flush=True)

    if not SpeechResult:
        response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="mr-IN">फसलमित्र मध्ये आपले स्वागत आहे. कृपया तुमचा शेतीविषयक किंवा पिकाबद्दलचा प्रश्न बोला.</Say>
    <Gather input="speech" timeout="6" action="/api/v1/webhooks/phone" language="mr-IN"/>
</Response>"""
        return Response(content=response_xml, media_type="application/xml")

    # If farmer spoke a question on phone
    advisory_req = AdvisoryQueryRequest(
        farmer_id=f"FARM-{Caller[-4:]}",
        channel="PHONE",
        language="mr",
        text=SpeechResult,
        location_district="Latur",
        location_state="Maharashtra"
    )

    pipeline_res = await process_advisory_query(advisory_req, db)

    response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="mr-IN">{pipeline_res.answer_text}</Say>
    <Pause length="1"/>
    <Say voice="alice" language="mr-IN">धन्यवाद! फसलमित्र सोबत जोडल्याबद्दल आभार.</Say>
</Response>"""

    return Response(content=response_xml, media_type="application/xml")
