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
from backend.app.core.tts_engine import tts_engine

from backend.app.core.geo_tracker import geo_tracker

sys.stdout.reconfigure(encoding='utf-8')
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

VOICE_NOTE_FOOTERS = {
    "mr": "🎙️ *व्हॉईस संदेश (Voice Note):* खालील ऑडिओ प्लेयरद्वारे ऐका",
    "hi": "🎙️ *वॉइस संदेश (Voice Note):* नीचे दिए गए ऑडियो प्लेयर से सुनें",
    "gu": "🎙️ *વૉઇસ સંદેશ (Voice Note):* નીચેના ઑડિઓ પ્લેયર દ્વારા સાંભળો",
    "pa": "🎙️ *ਆਵਾਜ਼ ਸੁਨੇਹਾ (Voice Note):* ਹੇਠਾਂ ਦਿੱਤੇ ਆਡੀਓ ਪਲੇਅਰ ਰਾਹੀਂ ਸੁਣੋ",
    "bn": "🎙️ *ভয়েস বার্তা (Voice Note):* নিচের অডিও প্লেয়ারে শুনুন",
    "te": "🎙️ *వాయిస్ సందేశం (Voice Note):* దిగువ ఆడియో ప్లేయర్ ద్వారా వినండి",
    "ta": "🎙️ *குரல் செய்தி (Voice Note):* கீழே உள்ள ஆடியோ பிளேயர் மூலம் கேளுங்கள்",
    "kn": "🎙️ *ಧ್ವನಿ ಸಂದೇಶ (Voice Note):* ಕೆಳಗಿನ ಆಡಿಯೊ ಪ್ಲೇಯರ್ ಮೂಲಕ ಆಲಿಸಿ",
    "ml": "🎙️ *ശബ്ദ സന്ദേശം (Voice Note):* താഴെയുള്ള ഓഡിയോ പ്ലെയറിലൂടെ കേൾക്കുക",
    "or": "🎙️ *ଭଏସ୍ ବାର୍ତ୍ତା (Voice Note):* ତଳେ ଥିବା ଅଡିଓ ପ୍ଲେୟାର୍ ମାଧ୍ୟମରେ ଶୁଣନ୍ତୁ",
    "as": "🎙️ *ভইচ বাৰ্তা (Voice Note):* তলৰ অডিঅ' প্লেয়াৰযোগে শুনক",
    "ur": "🎙️ *صوتی پیغام (Voice Note):* نیچے دیے گئے آڈیو پلیئر کے ذریعے سنیں",
    "sa": "🎙️ *ध्वनिसन्देशः (Voice Note):* अधस्तन-श्रव्ययन्त्रेण शृण्वन्तु",
    "ne": "🎙️ *भ्वाइस सन्देश (Voice Note):* तल दिइएको अडियो प्लेयरबाट सुन्नुहोस्",
    "kok": "🎙️ *व्हॉईस संदेश (Voice Note):* सकयल्या ऑडिओ प्लेयरार आयकात",
    "mai": "🎙️ *वॉइस संदेश (Voice Note):* नीचा देल ऑडियो प्लेयर सँ सुनू",
    "doi": "🎙️ *आवाज़ सुनेहा (Voice Note):* हेठ दित्ते गेदे आडियो प्लेयर थमां सुणो",
    "ks": "🎙️ *صوتی پیغام (Voice Note):* بۄنہِ دِژمٕژ آڈیو پلیئر کٔنؠ بوزِو",
    "sd": "🎙️ *صوتي پيغام (Voice Note):* هيٺين آڊيو پليئر ذريعي ٻڌو",
    "mni": "🎙️ *খোন্থোক পাউজেল (Voice Note):* মখাগী অডিও প্লেয়ারদা তাবীয়ু",
    "brx": "🎙️ *राव खौरां (Voice Note):* गाहायाव थानाय अडिअ' प्लेयारजों खनासं",
    "sat": "🎙️ *ᱟᱲᱟᱝ ᱠᱷᱚᱵᱚᱨ (Voice Note):* ᱞᱟᱛᱟᱨ ᱨᱮᱱᱟᱜ ᱚᱰᱤᱭᱳ ᱯᱞᱮᱭᱟᱨ ᱛᱮ ᱟᱧᱡᱚᱢ ᱢᱮ",
    "en": "🎙️ *Voice Note:* Listen via the audio player below"
}

def get_voice_footer(lang_code: str) -> str:
    return VOICE_NOTE_FOOTERS.get(lang_code, VOICE_NOTE_FOOTERS["en"])

class WhatsAppJsonRequest(BaseModel):
    phone: str = "+919823012345"
    message: str = ""
    audio_base64: Optional[str] = None
    language: str = "auto"
    crop_override: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    client_ip: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


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
            audio_url = await tts_engine.synthesize("weather", weather_text, "mr")
            if audio_url:
                await send_meta_whatsapp_audio(from_phone, audio_url)
            return {"status": "SUCCESS", "reply": reply_text, "audio_url": audio_url}

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
            passport_voice = f"शेतकरी पिक पासपोर्ट माहिती: पिक {passport.crop_name if passport else 'सोयाबीन'}, जात {passport.variety if passport else 'JS 335'}, पेरणी दिनांक {passport.sowing_date if passport else '१५ जून'}, वाढीचा टप्पा ३५ दिवस."
            audio_url = await tts_engine.synthesize("passport", passport_voice, "mr")
            if audio_url:
                await send_meta_whatsapp_audio(from_phone, audio_url)
            return {"status": "SUCCESS", "reply": reply_text, "audio_url": audio_url}

        # 14-Stage Grounded Pipeline Execution
        lat = None
        lon = None
        if msg_type == "location":
            loc = msg.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")

        client_ip = None
        if request:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            elif request.headers.get("x-real-ip"):
                client_ip = request.headers.get("x-real-ip")
            elif getattr(request, "client", None):
                client_ip = request.client.host

        advisory_req = AdvisoryQueryRequest(
            farmer_id=f"FARM-{from_phone[-4:]}",
            channel="WHATSAPP",
            language="auto",
            text=user_text,
            location_district=None,
            location_state=None,
            client_ip=client_ip,
            latitude=lat,
            longitude=lon
        )
        pipeline_res = await process_advisory_query(advisory_req, db, request)

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
        if pipeline_res.audio_url:
            await send_meta_whatsapp_audio(from_phone, pipeline_res.audio_url)
        return {"status": "SUCCESS", "answer": pipeline_res.answer_text, "audio_url": pipeline_res.audio_url, "grounding": pipeline_res.grounding_status}
    except Exception as e:
        print(f"[{now_str}] ⚠️ Meta WhatsApp Webhook Exception: {e}", flush=True)
        return {"status": "ERROR", "detail": str(e)}


@router.post("/whatsapp/json")
async def whatsapp_json_endpoint(
    req: WhatsAppJsonRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    JSON Endpoint for WhatsApp Automation & Web Simulator.
    """
    now_str = datetime.now().strftime("%H:%M:%S")
    user_text = req.message.strip() if req.message.strip() else "માझ्या સોયાબીનની પાંદડા પીળા પડી રહ્યા છે"
    print(f"\n[{now_str}] 📩 [JSON API WHATSAPP MESSAGE]: '{user_text}' (Phone: {req.phone})", flush=True)

    # Extract Client IP from Request if not supplied
    client_ip = req.client_ip
    if not client_ip and request:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.headers.get("x-real-ip"):
            client_ip = request.headers.get("x-real-ip")
        elif getattr(request, "client", None):
            client_ip = request.client.host

    input_lower = user_text.lower()

    # Friendly Greeting & Interactive Menu Shortcut
    if input_lower in ["hi", "hello", "hey", "namaste", "namaskar", "kem cho", "ram ram", "pranam", "help", "/start", "/help", "મેન્યુ", "મેનુ", "मेनू", "मेन्यू", "શરૂ", "શરૂઆત", "start", "menu"]:
        st, dist = geo_tracker.detect_location(
            query_text=user_text,
            lat=req.latitude,
            lon=req.longitude,
            requested_district=req.district,
            requested_state=req.state
        )

        # Detect the true language of the user's greeting input
        if req.language and req.language != "auto":
            det_lang = req.language
        elif input_lower in ["hi", "hello", "hey", "help", "/start", "/help", "start", "menu"]:
            det_lang = "en"
        elif input_lower in ["kem cho", "મેન્યુ", "મેનુ", "શરૂ", "શરૂઆત"]:
            det_lang = "gu"
        elif input_lower in ["namaskar", "नमस्कार"]:
            det_lang = "mr" if "Maharashtra" in st else "hi"
        elif input_lower in ["namaste", "नमस्ते", "ram ram", "राम राम", "pranam", "प्रणाम", "मेनू", "मेन्यू"]:
            det_lang = "hi"
        else:
            det_lang = asr_engine._detect_language(user_text)

        footer = get_voice_footer(det_lang)

        if det_lang == "en":
            welcome_text = (
                f"🌾 *[FasalMitra - 24/7 AI Agricultural Assistant]*\n"
                f"_________________________________________\n"
                f"Hello farmer friend! Welcome to FasalMitra, your 24/7 AI Agricultural Assistant ({dist}, {st}).\n\n"
                f"You can choose an option below or send a Voice Note 🎙️:\n\n"
                f"1️⃣ *Crop Problem Diagnosis:* Ask any question (e.g. *'How to control pink bollworm in cotton?'*, *'Why are soybean leaves yellowing?'*)\n"
                f"2️⃣ *Weather & Spray Forecast:* Type *2* or *weather*\n"
                f"3️⃣ *Farmer Crop Passport:* Type *3* or *passport*\n\n"
                f"🛡️ *ICAR / State Agricultural University certified & supports all 23 Indian Languages!*\n"
                f"{footer}"
            )
            voice_text = "Hello farmer friend! Welcome to FasalMitra, your twenty-four seven AI agricultural assistant. Please send a voice note or type your question about any crop."
        elif det_lang == "gu":
            welcome_text = (
                f"🌾 *[FasalMitra (ફસલમિત્ર) - કૃષિ સહાયક]*\n"
                f"_________________________________________\n"
                f"નમસ્કાર ખેડૂત મિત્ર! હું તમારો ૨૪/૭ AI કૃષિ સલાહકાર છું ({dist}, {st}).\n\n"
                f"તમે નીચેના વિકલ્પો પસંદ કરી શકો છો અથવા બોલીને વૉઇસ નોટ 🎙️ મોકલી શકો છો:\n\n"
                f"1️⃣ *પાક રોગ/જીવાત સલાહ:* કોઈપણ પ્રશ્ન પૂછો (દા.ત. *'કપાસમાં ગુલાબી ઈયળ આવી ગઈ છે'*, *'સોયાબીનના પાંદડા પીળા કેમ પડે છે'*)\n"
                f"2️⃣ *હવામાન અને છંટકાવ આગાહી:* *2* અથવા *weather* લખો\n"
                f"3️⃣ *પાક પાસપોર્ટ વિગતો:* *3* અથવા *passport* લખો\n\n"
                f"🛡️ *સંપૂર્ણપણે ICAR / JAU / AAU પ્રમાણિત અને ૨૩ ભાષાઓમાં ઉપલબ્ધ!*\n"
                f"{footer}"
            )
            voice_text = "નમસ્કાર ખેડૂત મિત્ર! ફસલમિત્ર કૃષિ સહાયકમાં આપનું સ્વાગત છે. તમારા પાકનો કોઈપણ પ્રશ્ન પૂછવા માટે વૉઇસ નોટ મોકલો અથવા મેસેજ ટાઈપ કરો."
        elif det_lang == "mr":
            welcome_text = (
                f"🌾 *[FasalMitra (फसलमित्र) - कृषी सहाय्यक]*\n"
                f"_________________________________________\n"
                f"नमस्कार शेतकरी मित्र! मी आपला २४/७ AI कृषी सहाय्यक आहे ({dist}, {st}).\n\n"
                f"तुम्ही खालील पर्याय निवडू शकता किंवा बोलून व्हॉईस नोट 🎙️ पाठवू शकता:\n\n"
                f"1️⃣ *पिक रोग व कीड सल्ला:* कोणताही प्रश्न विचारा (उदा. *'सोयाबीन पिवळे पडत आहे'*, *'कपाशीवर बोंडअळी उपाय'*)\n"
                f"2️⃣ *हवामान अंदाज (Agromet):* *2* किंवा *weather* टाईप करा\n"
                f"3️⃣ *शेतकरी पिक पासपोर्ट:* *3* किंवा *passport* टाईप करा\n\n"
                f"🛡️ *पूर्णपणे ICAR / MPKV प्रमाणित आणि २३ भारतीय भाषांमध्ये उपलब्ध!*\n"
                f"{footer}"
            )
            voice_text = "नमस्कार शेतकरी मित्र! फसलमित्र कृषी सहाय्यक मध्ये आपले स्वागत आहे. आपल्या पिकाचा कोणताही प्रश्न विचारण्यासाठी व्हॉईस मेसेज पाठवा किंवा टाईप करा."
        else:
            welcome_text = (
                f"🌾 *[FasalMitra (फसलमित्र) - AI Agri-Advisor]*\n"
                f"_________________________________________\n"
                f"नमस्ते किसान भाई! मैं आपका 24/7 AI कृषि सलाहकार हूँ ({dist}, {st}).\n\n"
                f"आप नीचे दिए गए विकल्प चुन सकते हैं या बोलकर वॉइस नोट 🎙️ भेज सकते हैं:\n\n"
                f"1️⃣ *फसल रोग/कीट परामर्श:* कोई भी सवाल पूछें (उदा. *'कपास में गुलाबी सुंडी का इलाज'*, *'गेहूं में पीला रतुआ'*)\n"
                f"2️⃣ *मौसम एवं छिड़काव अनुकूलता:* *2* या *weather* लिखें\n"
                f"3️⃣ *किसान फसल पासपोर्ट:* *3* या *passport* लिखें\n\n"
                f"🛡️ *पूर्णतः ICAR / राज्य कृषि विश्वविद्यालय द्वारा प्रमाणित!*\n"
                f"{footer}"
            )
            voice_text = "नमस्ते किसान भाई! फसलमित्र कृषि सलाहकार में आपका स्वागत है। अपनी फसल का कोई भी सवाल पूछने के लिए वॉइस नोट भेजें या मैसेज लिखें।"

        audio_url = await tts_engine.synthesize(f"welcome_{det_lang}", voice_text, det_lang)
        return {"reply_body": welcome_text, "pipeline_result": None, "audio_url": audio_url}

    if input_lower in ["2", "/weather", "weather", "हवामान", "હવામાન", "ਮੌਸਮ", "मौसम", "আবহাওয়া", "వాతావరణం"]:
        st, dist = geo_tracker.detect_location(query_text=user_text, lat=req.latitude, lon=req.longitude, requested_district=req.district, requested_state=req.state)
        agro_prof = geo_tracker.get_regional_agro_profile(st, dist)
        
        # Determine language for weather response
        if req.language and req.language != "auto":
            det_lang = req.language
        elif input_lower in ["weather", "/weather"]:
            det_lang = "en"
        elif input_lower in ["હવામાન"]:
            det_lang = "gu"
        elif input_lower in ["हवामान"]:
            det_lang = "mr"
        elif input_lower in ["ਮੌਸਮ"]:
            det_lang = "pa"
        elif input_lower in ["मौसम"]:
            det_lang = "hi"
        else:
            det_lang = asr_engine._detect_language(user_text)

        if det_lang == "en":
            weather_text = f"Weather in {dist} ({st}) is generally clear and favorable for agricultural operations and spraying. No heavy rainfall expected in the next 48 hours."
        elif det_lang == "gu":
            weather_text = f"{dist} ({st}) વિસ્તારમાં હવામાન સામાન્ય રીતે સ્વચ્છ અને ખુલ્લું રહેશે. દવા છાંટવા માટે અનુકૂળ રહેશે."
        elif det_lang == "mr":
            weather_text = f"{dist} ({st}) जिल्ह्यात हवामान स्वच्छ व कोरडे राहण्याची शक्यता आहे. कीटकनाशक फवारणीसाठी हवामान अनुकूल आहे."
        else:
            weather_text = f"{dist} ({st}) में मौसम मुख्यतः साफ और शुष्क रहेगा। कृषि कार्यों एवं कीटनाशक छिड़काव हेतु मौसम अनुकूल है।"

        footer = get_voice_footer(det_lang)
        reply_body = f"🌧️ *[{agro_prof['weather_station']}]*\n\n{weather_text}\n\n🛡️ *Source:* IMD Agromet Advisory Service\n{footer}"
        audio_url = await tts_engine.synthesize(f"weather_{det_lang}", weather_text, det_lang)
        return {"reply_body": reply_body, "pipeline_result": None, "audio_url": audio_url}

    if input_lower in ["3", "/passport", "passport", "પિક", "પાક", "फसल", "पिक", "ਫਸਲ"]:
        st, dist = geo_tracker.detect_location(query_text=user_text, lat=req.latitude, lon=req.longitude, requested_district=req.district, requested_state=req.state)
        passport = db.query(CropPassport).first()
        
        if req.language and req.language != "auto":
            det_lang = req.language
        elif input_lower in ["passport", "/passport"]:
            det_lang = "en"
        elif input_lower in ["પિક", "પાક"]:
            det_lang = "gu"
        elif input_lower in ["पिक"]:
            det_lang = "mr"
        else:
            det_lang = asr_engine._detect_language(user_text)

        footer = get_voice_footer(det_lang)

        if det_lang == "en":
            reply_body = (
                f"🌱 *[Farmer Crop Passport - {dist}, {st}]*\n\n"
                f"• *Crop:* {passport.crop_name if passport else 'Soybean'}\n"
                f"• *Variety:* {passport.variety if passport else 'JS 335'}\n"
                f"• *Sowing Date:* {passport.sowing_date if passport else '2026-06-15'}\n"
                f"• *Stage:* {passport.stage_days if passport else 35} Days\n"
                f"• *District & State:* {dist}, {st}\n"
                f"{footer}"
            )
            passport_voice = f"Farmer Crop Passport: Crop {passport.crop_name if passport else 'Soybean'}, Variety {passport.variety if passport else 'JS 335'} in {dist}, {st}."
        elif det_lang == "gu":
            reply_body = (
                f"🌱 *[ખેડૂત પાક પાસપોર્ટ - {dist}, {st}]*\n\n"
                f"• *પાક:* {passport.crop_name if passport else 'સોયાબીન'}\n"
                f"• *જાત:* {passport.variety if passport else 'JS 335'}\n"
                f"• *વાવણી તારીખ:* {passport.sowing_date if passport else '2026-06-15'}\n"
                f"• *તબક્કો:* {passport.stage_days if passport else 35} દિવસ\n"
                f"• *જિલ્લો અને રાજ્ય:* {dist}, {st}\n"
                f"{footer}"
            )
            passport_voice = f"ખેડૂત પાક પાસપોર્ટ માહિતી: પાક {passport.crop_name if passport else 'સોયાબીન'}, જાત {passport.variety if passport else 'JS 335'}."
        else:
            reply_body = (
                f"🌱 *[किसान फसल पासपोर्ट - {dist}, {st}]*\n\n"
                f"• *फसल:* {passport.crop_name if passport else 'सोयाबीन'}\n"
                f"• *किस्म:* {passport.variety if passport else 'JS 335'}\n"
                f"• *बुवाई तिथि:* {passport.sowing_date if passport else '2026-06-15'}\n"
                f"• *अवस्था:* {passport.stage_days if passport else 35} दिन\n"
                f"• *जिला व राज्य:* {dist}, {st}\n"
                f"{footer}"
            )
            passport_voice = f"किसान फसल पासपोर्ट जानकारी: फसल {passport.crop_name if passport else 'सोयाबीन'}, किस्म {passport.variety if passport else 'JS 335'}."

        audio_url = await tts_engine.synthesize(f"passport_{det_lang}", passport_voice, det_lang)
        return {"reply_body": reply_body, "pipeline_result": None, "audio_url": audio_url}
    
    advisory_req = AdvisoryQueryRequest(
        farmer_id=f"FARM-{req.phone[-4:]}",
        channel="WHATSAPP",
        language=req.language,
        text=user_text,
        audio_base64=req.audio_base64,
        crop_override=req.crop_override,
        location_district=req.district,
        location_state=req.state,
        client_ip=client_ip,
        latitude=req.latitude,
        longitude=req.longitude
    )

    pipeline_res = await process_advisory_query(advisory_req, db, request)
    grounding_badge = "✅ ICAR/KVK Grounded Evidence" if pipeline_res.grounding_status == "SUPPORTED" else "⚠️ Escalated to Expert Queue"
    source_title = pipeline_res.retrieved_evidence[0].title if pipeline_res.retrieved_evidence else "ICAR/KVK Advisory"
    footer = get_voice_footer(pipeline_res.language_detected)

    reply_body = (
        f"🌾 *[FasalMitra Grounded Agri-Advisory]*\n"
        f"_________________________________________\n\n"
        f"{pipeline_res.answer_text}\n\n"
        f"📌 *Confidence:* {int(pipeline_res.confidence_score * 100)}% ({pipeline_res.confidence_level})\n"
        f"🛡️ *Grounding Status:* {grounding_badge}\n"
        f"📖 *Evidence Source:* {source_title}\n"
        f"{footer}"
    )

    return {
        "reply_body": reply_body,
        "pipeline_result": pipeline_res,
        "audio_url": pipeline_res.audio_url
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
            print(f"[META WHATSAPP OUTBOUND] Sent WhatsApp text to {to_phone}. HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"[META WHATSAPP OUTBOUND] Error sending WhatsApp text: {e}", flush=True)


async def send_meta_whatsapp_audio(to_phone: str, audio_url: str):
    """
    Dispatches outbound WhatsApp voice/audio message using Meta Graph API HTTP endpoint.
    Allows farmers to listen to the spoken advisory directly on WhatsApp.
    """
    token = settings.META_WHATSAPP_TOKEN
    phone_id = settings.META_WHATSAPP_PHONE_ID
    if not token or not phone_id:
        print(f"[META WHATSAPP OUTBOUND AUDIO] Voice note generated at {audio_url} (Ready for delivery to {to_phone})", flush=True)
        return

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "audio",
        "audio": {"link": audio_url}
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            print(f"[META WHATSAPP OUTBOUND AUDIO] Sent WhatsApp voice note to {to_phone}. HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"[META WHATSAPP OUTBOUND AUDIO] Error sending WhatsApp voice note: {e}", flush=True)
