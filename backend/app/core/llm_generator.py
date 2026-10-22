import os
import httpx
import re
from typing import List, Dict, Optional
from backend.app.schemas.schemas import EvidenceChunk
from backend.app.config import settings

CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest"
]


class GroundedLLMGenerator:
    async def generate_response(
        self,
        user_query: str,
        evidence: List[EvidenceChunk],
        crop: str,
        stage_name: str,
        weather_info: str,
        language: str = "mr",
        conversation_history: List[Dict[str, str]] = None,
        location_info: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generates comprehensive, grounded agronomist advisory strictly utilizing
        retrieved ICAR/KVK/KCC evidence context via modern Gemini Flash LLM.
        """
        evidence_text = "\n\n".join([f"Official Evidence [{e.authority} - {e.title}]:\n{e.text}" for e in evidence])
        
        history_text = ""
        if conversation_history:
            history_text = "\nRecent Conversation History:\n" + "\n".join(
                [f"{h.get('sender', 'FARMER')}: {h.get('text', '')}" for h in conversation_history[-4:]]
            ) + "\n"

        lang_names = {
            "hi": "Hindi (हिंदी)",
            "mr": "Marathi (मराठी)",
            "gu": "Gujarati (ગુજરાતી)",
            "en": "English",
            "bn": "Bengali (বাংলা)",
            "te": "Telugu (తెలుగు)",
            "ta": "Tamil (தமிழ்)",
            "kn": "Kannada (ಕನ್ನಡ)",
            "ml": "Malayalam (മലയാളം)",
            "pa": "Punjabi (ਪੰਜਾਬੀ)",
            "or": "Odia (ଓଡ଼ିଆ)",
            "as": "Assamese (অসমীয়া)",
            "ur": "Urdu (اردو)",
            "sa": "Sanskrit (संस्कृतम्)",
            "ks": "Kashmiri (कश्मीरी / كٲଶُر)",
            "sd": "Sindhi (सिन्धी / سنڌي)",
            "ne": "Nepali (नेपाली)",
            "kok": "Konkani (कोंकणी)",
            "mai": "Maithili (मैथिली)",
            "doi": "Dogri (डोगरी)",
            "mni": "Manipuri (মৈতৈলোন্ / Meitei)",
            "brx": "Bodo (बड़ो)",
            "sat": "Santali (संताली / ᱥᱟᱱᱛᱟᱲᱤ)"
        }
        target_lang_name = lang_names.get(language, "Hindi (हिंदी)")

        loc_str = ""
        state = "India"
        dist = ""
        auth = ""
        scheme = ""
        if location_info:
            state = location_info.get("state", "India")
            dist = location_info.get("district", "")
            auth = location_info.get("authorities", "")
            scheme = location_info.get("portal_scheme", "")
            loc_str = f"• Location: {dist}, {state}\n• Regional Authority / State Agricultural University: {auth}\n• Government Agricultural Portals/Schemes: {scheme}\n"

        system_prompt = (
            f"You are FasalMitra (फसलमित्र), an expert senior agricultural advisor and ICAR/KVK certified agronomist helping Indian farmers across all 28 states and Union Territories.\n\n"
            f"MANDATORY INSTRUCTIONS:\n"
            f"1. LANGUAGE: You MUST write your ENTIRE response fluently, naturally, and warmly in {target_lang_name} using its correct native script. Do NOT switch to English or mixed languages unless scientific product trade names.\n"
            f"2. GROUNDING & REGIONAL ACCURACY: Ground your diagnosis, treatment, varieties, spray schedules, and dosages strictly in official agricultural evidence tailored to the farmer's state ({state} - e.g. state Agricultural Universities {auth} and government portals {scheme}).\n"
            f"3. THOROUGHNESS & DEPTH:\n"
            f"   - Explain the CAUSE (Why this pest/disease/deficiency occurs - lifecycle, temperature, humidity).\n"
            f"   - Detail the ACTION PLAN / PROCESS (Step 1, Step 2, Step 3 clearly formatted with bullet points).\n"
            f"   - Include APPROVED REMEDIES & EXACT DOSAGES (active ingredient name, standard formulations, and exact ml/g per liter of water or per acre/hectare as stated in evidence).\n"
            f"   - Add WEATHER & SAFETY PRECAUTIONS (spray timing, PPE, waiting period before harvest).\n"
            f"4. FORMATTING: Use clean bullet points, bold key terms, and maintain a respectful, empathetic tone for the farmer.\n\n"
            f"Farmer Context:\n"
            f"• Crop: {crop}\n"
            f"• Crop Stage: {stage_name}\n"
            f"{loc_str}"
            f"• Current Weather: {weather_info}\n"
            f"{history_text}\n"
            f"Official Agricultural Evidence (ICAR/KVK/KCC):\n"
            f"{evidence_text}\n\n"
            f"Farmer's Question: {user_query}\n\n"
            f"Deliver a complete, high-quality, practical agronomist advisory in {target_lang_name}:"
        )

        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

        # 1. Live Google Gemini API Integration with Multi-Model Fallback
        if gemini_key:
            async with httpx.AsyncClient(timeout=22.0) as client:
                for model_name in CANDIDATE_MODELS:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                    payload = {
                        "contents": [{"parts": [{"text": system_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 1024
                        }
                    }
                    try:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            res_data = resp.json()
                            candidates = res_data.get("candidates", [])
                            if candidates:
                                generated_text = candidates[0]["content"]["parts"][0]["text"].strip()
                                return generated_text
                        else:
                            print(f"[LLMGenerator] {model_name} HTTP {resp.status_code}, trying next model...", flush=True)
                    except Exception as e:
                        print(f"[LLMGenerator] {model_name} error ({type(e).__name__}): {e or 'Request timed out'}, trying next model...", flush=True)

        # 2. Deterministic High-Quality Fallback if API is offline
        return self._generate_deterministic_fallback(evidence, user_query, language, crop, stage_name)

    def _generate_deterministic_fallback(
        self,
        evidence: List[EvidenceChunk],
        user_query: str,
        language: str,
        crop: str,
        stage_name: str
    ) -> str:
        """Deterministic synthesis directly extracted from verified official evidence text in all 23 Indian languages."""
        if not evidence:
            no_info_msg = {
                "mr": "या प्रश्नावर आमच्याकडे अधिकृत पुरावा उपलब्ध नाही. कृपया जवळच्या कृषी विज्ञान केंद्राशी संपर्क साधावा.",
                "hi": "इस प्रश्न पर हमारे पास आधिकारिक प्रमाण उपलब्ध नहीं है। कृपया नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।",
                "gu": "આ પ્રશ્ન પર અમારી પાસે અધિકૃત પુરાવા નથી. કૃપા કરીને નજીકના કૃષિ વિજ્ઞાન કેન્દ્રનો સંપર્ક કરો.",
                "pa": "ਇਸ ਸਵਾਲ 'ਤੇ ਸਾਡੇ ਕੋਲ ਅਧਿਕਾਰਤ ਜਾਣਕਾਰੀ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਨਜ਼ਦੀਕੀ ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
                "bn": "এই প্রশ্নের জন্য সরকারি প্রমাণ উপলব্ধ নেই। অনুগ্রহ করে নিকটস্থ কৃষি বিজ্ঞান কেন্দ্রের সাথে যোগাযোগ করুন।",
                "te": "ఈ ప్రశ్నకు అధికారిక ఆధారాలు అందుబాటులో లేవు. దయచేసి సమీపంలోని కృషి విజ్ఞాన కేంద్రాన్ని సంప్రదించండి.",
                "ta": "இந்தக் கேள்விக்கு அதிகாரப்பூர்வ சான்றுகள் இல்லை. அருகிலுள்ள வேளாண் அறிவியல் மையத்தைத் தொடர்பு கொள்ளவும்.",
                "kn": "ಈ ಪ್ರಶ್ನೆಗೆ ಅಧಿಕೃತ ಪುರಾವೆ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಹತ್ತಿರದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                "ml": "ഈ ചോദ്യത്തിന് ഔദ്യോഗിക വിവരങ്ങൾ ലഭ്യമല്ല. ദയവായി അടുത്തുള്ള കൃഷി വിജ്ഞാന കേന്ദ്രവുമായി ബന്ധപ്പെടുക.",
                "or": "ଏହି ପ୍ରଶ୍ନ ପାଇଁ ସରକାରୀ ପ୍ରମାଣ ଉପଲବ୍ଧ ନାହିଁ। ଦୟାକରି ନିକଟସ୍ଥ କୃଷି ବିଜ୍ଞାନ କେନ୍ଦ୍ର ସହିତ ଯୋଗାଯୋଗ କରନ୍ତୁ।",
                "as": "এই প্ৰশ্নৰ বাবে চৰকাৰী তথ্য উপলব্ধ নহয়। অনুগ্ৰহ কৰি ওচৰৰ কৃষি বিজ্ঞান কেন্দ্ৰৰ সৈতে যোগাযোগ কৰক।",
                "ur": "اس سوال پر سرکاری ثبوت دستیاب نہیں ہے۔ براہ کرم قریبی کرشی وگیان کیندر سے رابطہ کریں۔",
                "sa": "अस्मिन् प्रश्ने अधिकृतप्रमाणं नास्ति। कृपया निकटे कृषि विज्ञान केन्द्रं सम्पृच्छन्तु।",
                "ne": "यस प्रश्नको आधिकारिक प्रमाण उपलब्ध छैन। कृपया नजिकको कृषि विज्ञान केन्द्रमा सम्पर्क गर्नुहोस्।",
                "kok": "ह्या प्रश्नाचेर अधिकृत पुरावे उपलब्ध नात. लागींच्या कृषी विज्ञान केंद्रा कडेन संपर्क करात.",
                "mai": "एहि प्रश्न पर आधिकारिक प्रमाण उपलब्ध नहि अछि। कृपया नजदीकी कृषि विज्ञान केंद्र सँ संपर्क करू।",
                "doi": "इस सवाल उप्पर सरकारी जानकारी नेईं ऐ। नेड़े दे कृषि विज्ञान केंद्र कन्नै संपर्क करो।",
                "ks": "امِ سوالس پیٹھ چھُنہٕ سرکاری ثبوت دستیاب۔ مہربٲنی کٔرِتھ نزدیٖکی کے وی کے سٟتؠ رابطہ کٔرِو।",
                "sd": "هن سوال تي سرڪاري ثبوت موجود ناهي. مهرباني ڪري ويجهي زرعي سائنس مرڪز سان رابطو ڪريو.",
                "mni": "মসিগী ৱাহং অসিগীদমক সর্কারগী চে-চাং লৈতে। নকপদা লৈবা ক্রিশি বিজ্ঞান কেন্দ্রদা ৱাফম থমবীয়ু।",
                "brx": "बे सोंथियाव सरकारी रोखायै फोरमान गैया। दया खालामना खाथिनि कृषि विज्ञान केन्द्रजों रायज्लाय।",
                "sat": "ᱱᱚᱣᱟ ᱠᱩᱠᱞᱤ ᱨᱮ ᱥᱚᱨᱠᱟᱨᱤ ᱥᱟᱹᱠᱷᱤ ᱵᱟᱹᱱᱩᱜᱼᱟ᱾ ᱫᱟᱭᱟᱠᱟᱛᱮ ᱥᱩᱨ ᱨᱮᱱᱟᱜ ᱠᱨᱤᱥᱤ ᱵᱤᱜᱽᱭᱟᱱ ᱠᱮᱱᱫᱽᱨᱚ ᱨᱮ ᱥᱟᱹᱜᱟᱹᱭ ᱡᱚᱲᱟᱣ ᱢᱮ᱾",
                "en": "Insufficient evidence to answer this question. Please consult your nearest Krishi Vigyan Kendra."
            }
            return no_info_msg.get(language, no_info_msg["en"])

        top_evidence = evidence[0]
        clean_text = top_evidence.text
        clean_text = re.sub(r'Farmer Question:.*?\n', '', clean_text)
        clean_text = re.sub(r'Official KCC Agronomist Recommendation:\s*', '', clean_text)
        clean_text = clean_text.strip()

        lang_headers = {
            "mr": f"🌱 **फसलमित्र कृषी सल्ला ({crop} - {top_evidence.title})**\n\n📌 **अधिकृत शिफारस ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **टीप:** फवारणी करताना जमिनीत पुरेशी ओलावा असावी आणि पाऊस पडण्याची शक्यता असल्यास फवारणी पुढे ढकलावी.",
            "hi": f"🌱 **फसलमित्र कृषि परामर्श ({crop} - {top_evidence.title})**\n\n📌 **आधिकारिक संस्तुति ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **सुझाव:** छिड़काव के समय खेत में पर्याप्त नमी रखें और मौसम साफ होने पर ही छिड़काव करें।",
            "gu": f"🌱 **ફસલમિત્ર કૃષિ સલાહ ({crop} - {top_evidence.title})**\n\n📌 **અધિકૃત ભલામણ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **સૂચના:** દવા છાંટતી વખતે જમીનમાં ભેજ હોવો જરૂરી છે અને વરસાદની શક્યતા હોય ત્યારે છંટકાવ મોકૂફ રાખવો.",
            "pa": f"🌱 **ਫਸਲਮਿੱਤਰ ਖੇਤੀਬਾੜੀ ਸਲਾਹ ({crop} - {top_evidence.title})**\n\n📌 **ਅਧਿਕਾਰਤ ਸਿਫ਼ਾਰਸ਼ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **ਸਾਵਧਾਨੀ:** ਸਪਰੇਅ ਕਰਨ ਸਮੇਂ ਖੇਤ ਵਿੱਚ ਢੁਕਵੀਂ ਨਮੀ ਹੋਣੀ ਚਾਹੀਦੀ ਹੈ ਅਤੇ ਮੌਸਮ ਸਾਫ਼ ਹੋਣ 'ਤੇ ਹੀ ਸਪਰੇਅ ਕਰੋ।",
            "bn": f"🌱 **ফসলমিত্র কৃষি পরামর্শ ({crop} - {top_evidence.title})**\n\n📌 **অনুমোদিত সুপারিশ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **সতর্কতা:** স্প্রে করার সময় জমিতে পর্যাপ্ত আর্দ্রতা রাখুন এবং বৃষ্টির সম্ভাবনা থাকলে স্প্রে স্থগিত রাখুন।",
            "te": f"🌱 **ఫసల్‌మిత్ర వ్యవసాయ సలహా ({crop} - {top_evidence.title})**\n\n📌 **అధికారిక సిఫార్సు ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **ముందస్తు జాగ్రత్త:** పిచికారీ చేసేటప్పుడు భూమిలో తగినంత తేమ ఉండాలి మరియు వాతావరణం అనుకూలంగా ఉన్నప్పుడే పిచికారీ చేయండి.",
            "ta": f"🌱 **பசல்மித்ரா வேளாண் ஆலோசனை ({crop} - {top_evidence.title})**\n\n📌 **அதிகாரப்பூர்வ பரிந்துரை ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **முன்னெச்சரிக்கை:** தெளிக்கும் போது நிலத்தில் போதுமான ஈரப்பதம் இருக்க வேண்டும் மற்றும் மழை இல்லாத போது தெளிக்கவும்.",
            "kn": f"🌱 **ಫಸಲ್‌ಮಿತ್ರ ಕೃಷಿ ಸಲಹೆ ({crop} - {top_evidence.title})**\n\n📌 **ಅಧಿಕೃತ ಶಿಫಾರಸು ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **ಮುನ್ನೆಚ್ಚರಿಕೆ:** ಸಿಂಪಡಿಸುವಾಗ ಮಣ್ಣಿನಲ್ಲಿ ಸಾಕಷ್ಟು ತೇವಾಂಶವಿರಲಿ ಮತ್ತು ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆಯಿದ್ದಾಗ ಸಿಂಪಡಿಸಬೇಡಿ.",
            "ml": f"🌱 **ഫസൽമിത്ര കാർഷിക നിർദ്ദേശം ({crop} - {top_evidence.title})**\n\n📌 **ഔദ്യോഗിക ശുപാർശ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **മുൻകരുതൽ:** മരുന്ന് തളിക്കുമ്പോൾ മണ്ണിൽ ആവശ്യത്തിന് ഈർപ്പം ഉണ്ടെന്ന് ഉറപ്പാക്കുക.",
            "or": f"🌱 **ଫସଲମିତ୍ର କୃଷି ପରାମର୍ଶ ({crop} - {top_evidence.title})**\n\n📌 **ଅଧିକୃତ ସୁପାରିଶ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **ସତର୍କତା:** ସ୍ପ୍ରେ କରିବା ସମୟରେ ଜମିରେ ଉପଯୁକ୍ତ ଆର୍ଦ୍ରତା ରଖନ୍ତୁ।",
            "as": f"🌱 **ফচলমিত্ৰ কৃষি পৰামৰ্শ ({crop} - {top_evidence.title})**\n\n📌 **অনুমোদিত অনুমোদন ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **সাৱধানতা:** স্প্ৰে কৰাৰ সময়ত মাটিত প্ৰয়োজনীয় আৰ্দ্ৰতা ৰাখিব।",
            "ur": f"🌱 **فصل مترا زرعی مشورہ ({crop} - {top_evidence.title})**\n\n📌 **سرکاری سفارش ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **احتیاط:** اسپرے کے وقت کھیت میں مناسب نمی رکھیں اور بارش سے پہلے اسپرے نہ کریں۔",
            "sa": f"🌱 **फसलमित्र कृषि परामर्शः ({crop} - {top_evidence.title})**\n\n📌 **अधिकृत संस्तुतिः ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **निर्देशः:** सेचनकाले भूमौ आर्द्रता आवश्यकी।",
            "ne": f"🌱 **फसलमित्र कृषि सल्लाह ({crop} - {top_evidence.title})**\n\n📌 **आधिकारिक सिफारिस ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **सुझाव:** विषादी छर्कँदा माटोमा पर्याप्त चिस्यान हुनुपर्छ।",
            "kok": f"🌱 **फसलमित्र शेती सल्‍लो ({crop} - {top_evidence.title})**\n\n📌 **अधिकृत शिफारस ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **शिटकावणी:** फवारणी करतना जमनीत पुरेशी ओल आसची.",
            "mai": f"🌱 **फसलमित्र कृषि सलाह ({crop} - {top_evidence.title})**\n\n📌 **आधिकारिक संस्तुति ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **सुझाव:** छिड़कावक समय खेत में नमी रहब जरूरी अछि।",
            "doi": f"🌱 **फसलमित्र कृषि सलाह ({crop} - {top_evidence.title})**\n\n📌 **सरकारी सिफ़ारिश ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **चेतावनी:** स्प्रे करदे वेले जमीन च नमी होनी चाहिदी।",
            "ks": f"🌱 **فصل مترا زراعت مشورہ ({crop} - {top_evidence.title})**\n\n📌 **سرکاری سفارش ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **احتیاط:** سپرے کرنہٕ وزِ پزِ زمینس منٛز نمی آسٕنؠ۔",
            "sd": f"🌱 **فصل مترا زرعي صلاح ({crop} - {top_evidence.title})**\n\n📌 **سرڪاري سفارش ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **احتياط:** ڦوهاري وقت زمين ۾ آلاڻ هجڻ ضروري آهي.",
            "mni": f"🌱 **ফসলমিত্র লৌউ-শিংউগী পাউতাক ({crop} - {top_evidence.title})**\n\n📌 **অফিসিয়েল পাউতাক ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **চেকশিনবা:** হিদাক কাপ্পদা লমদম অসিদা ঈশিং লেংদনা লৈগদবনি।",
            "brx": f"🌱 **फसलमित्र आबाद बिथिंखौ ({crop} - {top_evidence.title})**\n\n📌 **सरकारी बिथिंखौ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **सावधानी:** स्प्रे खालामनाय समाव हायाव सिदोब थानांगौ।",
            "sat": f"🌱 **ᱯᱷᱚᱥᱚᱞᱢᱤᱛᱨᱚ ᱪᱟᱥ ᱫᱤᱥᱟᱹ ({crop} - {top_evidence.title})**\n\n📌 **ᱥᱚᱨᱠᱟᱨᱤ ᱫᱤᱥᱟᱹ ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **ᱦᱩᱥᱤᱭᱟᱹᱨ:** ᱨᱟᱱ ᱪᱷᱤᱴᱠᱟᱹᱣ ᱡᱚᱠᱷᱮᱡ ᱦᱟᱥᱟ ᱨᱮ ᱫᱟᱜ ᱛᱟᱦᱮᱸᱱ ᱞᱟᱹᱠᱛᱤᱭᱟᱱᱟ᱾",
            "en": f"🌱 **FasalMitra Agricultural Advisory ({crop} - {top_evidence.title})**\n\n📌 **Official Recommendation ({top_evidence.authority}):**\n{clean_text}\n\n⚠️ **Precaution:** Ensure adequate soil moisture during application and avoid spraying before rainfall."
        }

        return lang_headers.get(language, lang_headers["en"])

llm_generator = GroundedLLMGenerator()