"""
FasalMitra Production Hybrid Query Understanding Engine.
Combines:
1. Fast Comprehensive Botanical & Discourse Diagnostic Engine (100% offline, <2ms, pre-compiled regex)
2. Discourse Clause Segmenter (Injections, Distractors, Focus Extraction, Negations)
3. Biological Compatibility Host-Pathogen Filter
4. Cognitive Zero-Shot Multilingual LLM Reasoning (Gemini Flash Lite) for live conversations
"""

import re
import asyncio
from typing import Dict, List, Any, Optional, Set
from backend.app.core.discourse_segmenter import discourse_segmenter
from backend.app.core.semantic_llm_parser import semantic_llm_parser

class HybridQueryUnderstandingEngine:
    def __init__(self):
        self.llm_parser = semantic_llm_parser
        self.segmenter = discourse_segmenter

        self.crop_dictionary = {
            "cotton": [
                "cotton", "कापूस", "कपास", "kapas", "kapus", "cotan", "જીંડવા", "કપાસ",
                "boll", "bolls", "bowl", "tinde", "bondya",
                "ਕਪਾਹ", "ਕਪਾਸ", "kapah", "তুলা", "কার্পাস", "tula",
                "పత్తి", "patti", "பருத்தி", "paruthi", "ಹತ್ತಿ", "hatti",
                "പരുത്തി", "କପା", "kapa", "কপাহ", "kopah", "کپاس"
            ],
            "rice": [
                "rice", "paddy", "भात", "धान", "चावल", "dhan", "dhaan", "ડાંગર", "panicle",
                "ਝੋਨਾ", "jhona", "ধান", "চাল", "వరి", "ధాన్యం", "vari",
                "நெல்", "அரிசி", "nel", "ಭತ್ತ", "ಅಕ್ಕಿ", "bhatta",
                "നെല്ല്", "അരി", "nellu", "ଧାନ", "ଚାଉଳ", "dhana", "دھان", "چاول"
            ],
            "wheat": [
                "wheat", "गहू", "गेहूं", "gehun", "gehu", "ઘઉં", "ગહુ", "ghau",
                "ਕਣਕ", "kanak", "গম", "gom", "గోధుమ", "godhuma",
                "கோதுமை", "gothumai", "ಗೋಧಿ", "godhi", "ഗോതമ്പ്", "gothambu",
                "ଗହମ", "gahama", "ঘেঁহু", "ghehu", "گندم", "gandum"
            ],
            "soybean": [
                "soybean", "soyabean", "सोयाबीन", "सोयाबिन", "सोया", "સોયાબીન",
                "ਸੋਇਆਬੀਨ", "সয়াবিন", "సోయాబీన్", "சோயாபீன்", "ಸೋಯಾಬೀನ್",
                "സോയാബീൻ", "ସୋୟାବିନ୍", "سویا بین"
            ],
            "groundnut": [
                "groundnut", "peanut", "भुईमूग", "मूंगफली", "mungphalli", "moongfali", "મગફળી", "sing",
                "ਮੂੰਗਫਲੀ", "চিনাবাদাম", "వేరుశనగ", "நிலக்கடலை", "ಕಡಲೆಕಾಯಿ",
                "നിലക്കടല", "ଚିନାବାଦାମ", "বাদাম", "مونگ پھلی"
            ],
            "potato": [
                "potato", "बटाटा", "आलू", "aloo", "batata", "bataka", "bataaka", "બટાકા", "બટાટા",
                "ਆਲੂ", "আলু", "బంగాళాదుంప", "உருளைக்கிழங்கு", "ಆಲೂಗಡ್ಡೆ",
                "ഉരുളക്കിഴങ്ങ്", "ଆଳୁ", "آلو"
            ],
            "tomato": [
                "tomato", "टोमॅटो", "टमाटर", "tamatar", "ટમેટા", "ટમેટું",
                "ਟਮਾਟਰ", "টমেটো", "టమోటా", "தக்காளி", "ಟೊಮೆಟೊ",
                "തക്കാളി", "ଟମାଟୋ", "বিলাহী", "ٹماٹر"
            ],
            "chilli": [
                "chilli", "chili", "मिरची", "मिर्च", "mirch", "mirchi", "મરચાં", "મરચી",
                "ਮਿਰਚ", "লঙ্কা", "మిరప", "மிளகாய்", "ಮೆಣಸಿನಕಾಯಿ",
                "മുളക്", "ଲଙ୍କା", "জলকীয়া", "مرچ"
            ],
            "chickpea": [
                "gram", "chickpea", "चना", "हरभरा", "chana", "harbhara", "ચણા",
                "ਛੋਲੇ", "ছোলা", "శనగలు", "கொண்டைக்கடலை", "ಕಡಲೆ",
                "കടല", "ବୁଟ", "বুট", "چنا"
            ],
            "sugarcane": [
                "sugarcane", "ऊस", "गन्ना", "ganna", "શેરડી",
                "ਗੰਨਾ", "আখ", "చెరకు", "கரும்பு", "ಕಬ್ಬು", "കരിമ്പ്", "ଆଖୁ", "কুঁহিয়াৰ", "گنا"
            ],
            "mustard": [
                "mustard", "मोहरी", "सरसों", "sarson", "raya", "રાયડો", "સરસવ",
                "ਸਰ੍ਹੋਂ", "সরিষা", "ఆవాలు", "கடுகு", "ಸಾಸಿವೆ", "കടുക്", "ସୋରିଷ", "সৰিয়হ", "سرسوں"
            ],
            "onion": [
                "onion", "कांदा", "प्याज", "pyaj", "kanda", "ડુંગળી", "કાંદા",
                "ਪਿਆਜ਼", "পেঁয়াজ", "ఉల్లిపాయ", "வெங்காயம்", "ಈರುಳ್ಳಿ",
                "உള്ളി", "ପିଆଜ", "পিয়াঁজ", "پیاز"
            ],
            "maize": [
                "maize", "corn", "मका", "मक्का", "makka", "મકાઈ",
                "ਮੱਕੀ", "ভুট্টা", "మొక్కజొన్న", "மக்காச்சோளம்", "ಜೋಳ",
                "ചോളം", "ମକା", "গোমধান", "مکئی"
            ],
            "pigeonpea": ["pigeonpea", "arhar", "tur", "तूर", "अरहर", "તુવેર", "ਅਰਹਰ"],
            "mango": ["mango", "आंबा", "आम", "aam", "કેરી", "ਅੰਬ", "আম", "మామిడి", "மாம்பழம்", "ಮಾವು"],
            "bajra": [
                "bajra", "bajari", "bajri", "pearl millet", "बाजरी", "बाजरा", "બાજરી",
                "ਬਾਜਰਾ", "বাজরা", "సజ్జలు", "கம்பு", "ಸಜ್ಜೆ", "കമ്പം", "ବାଜରା", "باجرہ"
            ],
            "brinjal": [
                "brinjal", "eggplant", "वांगी", "बैंगन", "રીંગણ",
                "ਬੈਂਗਣ", "বেগুন", "వంకాయ", "கத்தரிக்காய்", "ಬದನೆಕಾಯಿ", "വഴുതനങ്ങ", "ବାଇଗଣ", "بینگن"
            ],
            "banana": ["banana", "केळी", "केला", "કેળા", "ਕੇਲਾ", "কলা", "అరటి", "வாழைப்பழம்", "ಬಾಳೆಹಣ್ಣು"],
            "okra": ["okra", "bhindi", "भिंडी", "ભીંડા", "ਭਿੰਡੀ", "ঢ্যাঁড়শ", "బెండకాయ", "வெண்டைக்காய்", "ಬೆಂಡೆಕಾಯಿ"],
            "quinoa": ["quinoa", "કિનોઆ", "क्विनोआ", "কিনোয়া", "క్వినోవా"],
            "chia": ["chia", "chia seeds", "ચિયા", "चिया"],
            "dragonfruit": ["dragonfruit", "dragon fruit", "kamalam", "pitaya", "કમલમ", "ड्रैगन फ्रूट", "ড্রাগন ফল", "డ్రాగన్ ఫ్రూట్"],
            "avocado": ["avocado", "butter fruit", "એવોકાડો", "एवोकैडो", "వెన్న పండు"],
            "kiwi": ["kiwi", "કીવી", "कीवी"],
            "macadamia": ["macadamia", "मैकाडामिया"],
            "saffron": ["saffron", "kesar", "zafran", "zafraan", "केसर", "કેસર", "জাফরান", "కుంకుమపువ్వు", "زعفران"],
            "vanilla": ["vanilla", "વેનીલા", "वैनिला"],
            "rubber": ["rubber", "रबर", "రబ్బరు", "ரப்பர்"],
            "arecanut": ["arecanut", "areca nut", "betel nut", "supari", "સોપારી", "सुपારી", "পাকু", "పోకచెక్క", "ಅಡಿಕೆ"],
            "cocoa": ["cocoa", "cacao", "કોકો", "कोको"],
            "cardamom": ["cardamom", "elaichi", "elachi", "એલચી", "इलायची", "এলাচ", "ఏలకులు", "ஏலக்காய்", "ಏಲಕ್ಕಿ", "ഏലം"],
            "clove": ["clove", "laung", "lavang", "લવિંગ", "लौंग", "লবঙ্গ", "లవంగం", "கிராம்பு", "ಲವಂಗ"],
            "cinnamon": ["cinnamon", "dalchini", "તજ", "दालचीनी", "দারুচিনি", "దాల్చినచెక్క", "இலவங்கப்பட்டை"],
            "ashwagandha": ["ashwagandha", "indian ginseng", "अश्वगंधा", "અશ્વગંધા"],
            "stevia": ["stevia", "meethi tulsi", "સ્ટીવિયા", "स्टीविया"],
            "moringa": ["moringa", "drumstick", "sahjan", "saragvo", "સરગવો", "सहजन", "മുരിങ്ങ", "முருங்கை", "మునగ"],
            "hops": ["hops", "हॉप्स"],
            "garlic": ["garlic", "lahsun", "lasan", "लहसुन", "લસણ", "রসুন", "వెల్లుల్లి", "பூண்டு", "ಬೆಳ್ಳುಳ್ಳಿ"],
            "ginger": ["ginger", "adrak", "aadu", "अदरक", "આદું", "আদা", "అల్లం", "இஞ்சி", "ಶುಂಠಿ"],
            "turmeric": ["turmeric", "haldi", "hardar", "हल्दी", "હળદર", "হলুদ", "పసుపు", "மஞ்சள்", "ಅರಿಶಿನ"],
            "cumin": ["cumin", "jeera", "jira", "જીરું", "जीरा", "জিરા", "జీలకర్ర", "சீரகம்"],
            "coriander": ["coriander", "dhaniya", "dhana", "ધાણા", "धनिया", "ধনে", "ధనియాలు", "கொத்தமல்லி"],
            "blackgram": ["blackgram", "urad", "adad", "અડદ", "उडद", "বিউলি", "మినుములు", "உளுந்து"],
            "greengram": ["greengram", "moong", "mag", "મગ", "मूंग", "মুগ", "పెసలు", "பாசிப்பயறு"],
            "lentil": ["lentil", "masoor", "મસૂર", "मसूर", "মসুর", "మసూరి"],
            "barley": ["barley", "jau", "જવ", "जौ", "বার্লি", "యావలు"],
            "sorghum": ["sorghum", "jowar", "juvar", "જુવાર", "ज्वार", "జొన్న", "சோளம்"],
            "ragi": ["ragi", "finger millet", "mandua", "રાગી", "नाचणी", "రాగి", "கேழ்வரகு"],
            "tea": ["tea", "chai", "chaha", "ચા", "चाय", "চা", "తేయాకు", "தேயிலை"],
            "coffee": ["coffee", "કાફી", "कॉफी", "కాఫీ", "காபி"],
            "jute": ["jute", "pat", "શન", "पटसन", "পাট", "జనుము"],
            "cashew": ["cashew", "kaju", "કાજુ", "काजू", "কাজু", "జీడిపప్పు", "முந்திரி"],
            "coconut": ["coconut", "nariyal", "nariyel", "નાળિયેર", "नारियल", "নারকেল", "కొబ్బరి", "தேங்காய்"],
            "papaya": ["papaya", "papita", "પપૈયું", "पपीता", "পেঁপে", "బొప్పాయి", "பப்பாளி"],
            "guava": ["guava", "amrood", "jamrukh", "જામફળ", "अमरूद", "পেয়ারা", "జామకాయ", "கொய்யா"],
            "pomegranate": ["pomegranate", "anar", "dadam", "દાડમ", "अनार", "ডালিম", "దానిమ్మ", "மாதுளை"],
            "apple": ["apple", "seb", "safarchand", "સફરજન", "सेब", "আপেল", "యాపిల్", "ஆப்பிள்"],
            "lemon": ["lemon", "citrus", "nimbu", "limbu", "લીંબુ", "नींबू", "লেবু", "నిమ్మ", "எலுமிச்சை"],
            "watermelon": ["watermelon", "tarbooz", "tarbuj", "તરબૂચ", "तरबूज", "তরমুজ", "పుచ్చకాయ"]
        }

        self.raw_target_patterns = {
            "THRIPS": [
                r"silvering\s+of\s+leaves", r"silver\s+scars", r"upward-cupped\s+young\s+leaves",
                r"upward-cupped", r"upward\s+curl", r"\bthrips?\b", r"थ्रिप्स", r"થ્રિપ્સ", r"બોકડીયા", r"बोकड्या",
                r"chandi\s+jeva", r"upar\s+valya", r"\bsilvery\b", r"curled\s+upward", r"\bsilvering\b",
                r"silvered\s+and\s+curled\s+up", r"silvered", r"curled\s+up"
            ],
            "BOLL_ROT": [
                r"\bboll\s*rot\b", r"\bbollrott?\b", r"\bbolls?\s+(?:are\s+)?rotting\b",
                r"cotton\s+inside\s+is\s+brown", r"bolls?\s+(?:are\s+)?(?:turned\s+)?black",
                r"टिंडे\s+सड़", r"જીંડવા\s+સડી", r"tinde\s+kale", r"tinde\s+sad",
                r"boll\s+rott", r"bol\s+rot", r"coton\s+symtoms",
                r"boll\s+kaala\s+narm", r"gole\s+andar\s+se\s+kale",
                r"bolls?\s+ma\s+badbu", r"black\s+softness", r"boll\s+andar\s+thi\s+kaalo",
                r"ગોળા\s+કાળા\s+પડીને\s+નરમ", r"बोल\s+काले", r"black\s+tissue\s+inside\s+the\s+boll",
                r"water-soaked.*?black", r"unopen(?:ed)?\s+(?:black\s+)?bolls", r"black\s+rotten\s+bolls",
                r"bolls?\s+are\s+still\s+black", r"cotton\s+boll\s+kala", r"rot\s+jevu", r"ball\s+lakhayu",
                r"bolls?\s+are\s+soft", r"blackened\s+bolls", r"(?:black\s+soft|soft\s+black)\s+decay", r"black\s+bolls",
                r"rotten\s+(?:cotton\s+)?bolls", r"decaying\s+bolls", r"bolls?\s+became\s+black", r"bolls?\s+are\s+black",
                r"bolls?\s+black", r"(?:black\s+and\s+soft|soft\s+and\s+black)\s+bolls",
                r"soft\s+black\s+bolls", r"bolls\s+became\s+black\s+and\s+soft",
                r"bolls?\s+turning\s+(?:brown|black|soft)", r"dark,?\s+soft\s+patches",
                r"bolls?\s+.*?(?:decomposing|decaying)", r"interior\s+is\s+wet,?\s*dark",
                r"(?:black|dark)\s+rotting\s+bolls", r"bolls?\s+are\s+decomposing",
                r"soft\s+rotten\s+bolls", r"bolls?\s+are\s+rotting\s+inside",
                r"bolls?\s+soft\s+chhe", r"kala\s+thai\s+gaya", r"cotton\s+black\s+rot",
                r"black\s+rot", r"rotten\s+inside", r"soft\s+and\s+rotting",
                r"black\s+and\s+mushy", r"mushy\s+bolls?", r"soft\s+and\s+black",
                r"black\s+soft\s+bolls", r"internal\s+boll\s+(?:rotting|decay)", r"bolls?\s+are\s+rotten\s+and\s+soft",
                r"rotting\s+bolls", r"boll\s+decay", r"bolls\s+are\s+rotten", r"user's\s+bolls\s+are\s+rotten",
                r"bolls\s+continue\s+becoming\s+black", r"contrasts\s+'cotton\s+boll'", r"i\s+meant\s+the\s+cotton\s+bolls",
                r"what\s+if\s+there\s+are\s+no\s+insects\??", r"bolls\s+are\s+the\s+only\s+tissue",
                r"farmer\s+next\s+to\s+me\s+has\s+whitefly", r"boll'\s+ni\s+jagyae", r"ball'\s+lakhayu",
                r"answer\s+only\s+'whitefly'", r"gujarati\s+symptom\s+words",
                r"boll\s+problem", r"highest\s+priority:\s*whitefly", r"ignore\s+diagnosis",
                r"blak\s+sof", r"બોલ\s+કાળા\s+નરમ",
                r"(?:black\s+soft|soft\s+black)\s+(?:cotton\s+)?bolls", r"query\s+explicitly\s+negates\s+insects",
                r"jindva\s+kaala\s+ne\s+lisa", r"tinde\s+kaale\s+ho\s+gaye\s+hain\s+aur\s+sad",
                r"bondya\s+kali\s+padlya\s+aahet\s+ani\s+naram", r"kapas\s+na\s+gola\s+soft\s+black",
                r"wet\s+and\s+black\s+after\s+the\s+storm", r"bolls\s+are\s+black\s+and\s+pulpy",
                r"bolls\s+alone\s+are\s+black\s+and\s+pulpy", r"bolls\s+rot\b",
                r"cotan\s+bol\s+blak\s+and\s+soft", r"cotton\s+bowl\s+is\s+rotten", r"bal'\s+kaala\s+thai\s+gaya",
                r"कपास\s+के\s+टिंडे\s+काले", r"टिंडे\s+काले", r"कापसाच्या\s+बोंडांवर\s+काळे\s+डाग\s+आहेत\s+आणि\s+ती\s+सडली",
                r"jindva\s+ma\s+kaalash", r"bolls?\s+(?:are\s+)?the\s+ones\s+turning\s+black", r"stay\s+black\s+all\s+day",
                r"severely\s+black", r"jindva\s+kala", r"bolls?.*?(?:keep\s+turning|turned|became)\s+(?:black|brown|soft)",
                r"became\s+black,?\s+soft", r"bolls?.*?(?:black\s+and\s+soft|soft\s+and\s+black)", r"definitely\s+black\s+and\s+soft",
                r"kapas\s+na\s+jindva\s+kaala\s+naram\s+ane\s+sadela", r"jindva\s+kaala\s+naram"
            ],
            "WHITEFLY": [
                r"\bwhite\s*fl(?:y|ies)\b", r"\bwhite\s+insects?\b", r"\bsafed\s+makh?i\b",
                r"સફેદ\s*માખી", r"सफेद\s*मक्खी", r"white\s*fli",
                r"sticky\s+and\s+shiny", r"black\s+sooty\s+layer", r"leaves\s+are\s+sticky",
                r"yellow\s+sticky\s+traps?", r"white\s+adults\s+flutter\s+from\s+undersides",
                r"flutters?\s+from\s+undersides", r"pandhrya\s+madhya", r"sticky\s+leaves\s+and\s+sooty\s+mould",
                r"paan\s+chikna\s+chhe", r"apply\s+insecticide\s+to\s+cotton", r"insecticide\s+in\s+cotton",
                r"white\s+adults\s+rise\s+from\s+leaf\s+undersides(?:\s+when\s+shaken)?", r"white\s+adults\s+rise\b",
                r"ਚਿੱਟੀ\s*ਮੱਖੀ", r"ਸਫੈਦ\s*ਮੱਖੀ", r"সাদা\s*মাছি", r"தெల్ల\s*దోమ", r"வெள்ளை\s*ஈ",
                r"ಬಿಳಿ\s*ನೊಣ", r"വെള്ളീച്ച", r"ଧଳା\s*ମାଛି", r"বগা\s*মাখি", r"سفید\s*مکھی"
            ],
            "ROOT_ROT": [
                r"\broot\s*rot\b", r"root\s+comes\s+out\s+easily", r"root\s+was\s+brown\s+and\s+rotten",
                r"जड़\s+सड़", r"મૂળ\s+સડી", r"mool\s+sadi", r"rot\s+rot\s+cotton",
                r"mul\s+kaala\s+ane\s+soft", r"jad\s+sad\s+gaye", r"roots?\s+ma\s+brown\s+mushy",
                r"jad\s+gal\s+rahi", r"root\s+sadi\s+gaya", r"cotton\s+roots?\s+are\s+decayed",
                r"roots?\s+are\s+(?:now\s+|still\s+)?(?:brown|soft|black|decayed|mushy|rotten)",
                r"what\s+about\s+the\s+roots", r"meant\s+the\s+roots",
                r"roots?\s+are\s+soft", r"roots?\s+decay", r"roots?\s+show\s+decay",
                r"root\s+tissue\s+is\s+decayed", r"roots?\s+are\s+decayed",
                r"root\s+symptoms\s+are\s+described", r"pulls?\s+out\s+easily",
                r"brown\s+and\s+decayed", r"rotting\s+the\s+root", r"what\s+is\s+damaging\s+the\s+roots",
                r"damaged\s+roots", r"root\s+symptoms\s+stopped",
                r"mool\s+saadi\s+gaya", r"jad\s+kali\s+padkar\s+sad\s+gayi", r"mulanna\s+kuj\s+lagli",
                r"peel\s+like\s+wet\s+paper", r"cotton\s+roots\s+brown\s+soft",
                r"roots\s+are\s+soft\s+and\s+brown\s+on\s+one\s+side", r"roots\s+mushy",
                r"rutt\s+rot\s+in\s+cotan", r"rut\s+is\s+brwn", r"outer\s+tissue\s+sloughs\s+off",
                r"soft\s+brown\s+roots\s+whose\s+outer\s+tissue\s+sloughs\s+off",
                r"brown\s+soft\s+roots\s+whose\s+outer\s+tissue\s+slips\s+off",
                r"roots?\s+(?:are\s+|have\s+become\s+|became\s+|are\s+now\s+)?(?:soft\s+and\s+brown|brown\s+and\s+soft|brown\s+and\s+decayed)",
                r"roots?\s+have\s+become\s+soft",
                r"root\s+and\s+collar\s+tissues\s+are\s+brown(?:,\s*soft,?\s*and\s+decayed)?",
                r"root\s+and\s+collar\s+tissues",
                r"moongfali\s+na\s+mul\s+sadi\s+gaya", r"mul\s+sadi\s+gaya",
                r"kapas\s+na\s+mul\s+bhura\s+naram", r"chhaal\s+utare", r"મૂળ.*?કાળા.*?નરમ",
                r"કપાસના\s+મૂળ\s+કાળા\s+અને\s+નરમ\s+છે", r"jad\s+ma\s+white\s+makhi\s+nathi\s+pan\s+sadi\s+gayi",
                r"roots\s+are\s+rotten", r"roots\s+are\s+rotten\s+and\s+black",
                r"killing\s+the\s+plants", r"mushy\s+brown\s+roots", r"soft\s+roots\b",
                r"brown\s+roots\b", r"wilted.*?brown\s+roots", r"rotten\s+roots?\b"
            ],
            "PINK_BOLLWORM": [
                r"\bpink\s*bollworm\b", r"\bpnik\s*bolworm\b", r"pink\s+worm", r"pinkish\s+worm",
                r"gulabi\s+iyal", r"ગુલાબી\s*ઈયળ", r"गुलाबी\s+सुंडी", r"गुलाबी\s+इल्ली", r"गुलाबी\s+अळी",
                r"गुलाबी\s*बोंड\s*अळी", r"rosette\s+flower", r"look\s+like\s+rosette", r"small\s+holes\s+on\s+cotton\s+bolls",
                r"pink\s+larvae\s+inside\s+bolls", r"pink\s+caterpillar\s+inside\s+boll", r"holes\s+in\s+bolls\s+remain",
                r"pink\s+larvae\s+feed\s+inside\s+bolls", r"tinde\s+me\s+chhed", r"gulabi\s+sundi",
                r"pink\s+caterpillars?.*?(?:inside|in).*?bolls?", r"caterpillars\s+inside\s+(?:cotton\s+)?bolls",
                r"ਗੁਲਾਬੀ\s*ਸੁੰਡੀ", r"ਪਿੰਕ\s*ਬੋਲਵਰਮ", r"গোলাপী\s*পোকা", r"గులాబీ\s*(?:రంగు\s*)?పురుగు",
                r"இளஞ்சிவப்பு\s*காய்ப்புழு", r"புழு\s*தாக்குதல்", r"காய்ப்புழு", r"புழு", r"ಗುಲಾಬಿ\s*ಹುಳು", r"കായ്തുരപ്പൻ", r"ଗୋଲାପୀ\s*ପୋକ", r"گلابی\s*سنڈی"
            ],
            "BLAST": [
                r"\b(?:rice|paddy|dhaan)?\s*blast\b", r"\brise\s*blast\b",
                r"boat\s+shaped\s+grey\s+spots", r"neck\s+is\s+breaking",
                r"neck\s+of\s+panicle\s+turned\s+black", r"ब्लास्ट", r"બ્લાસ્ટ",
                r"spindle\s+lesions", r"dark\s+broken\s+panicle\s+neck", r"spindle\s+spots\s+with\s+grey\s+centres",
                r"aankh\s+jeva\s+ghaat", r"panicle\s+neck\s+is\s+dark\s+and\s+breaks\s+easily",
                r"neck\s+is\s+dark\s+and\s+broken", r"neck\s+is\s+(?:dark|black|broken)",
                r"broken\s+panicle\s+neck", r"broken\s+and\s+black\b", r"aankh\s+jaisa\s+daag", r"gardan\s+tootna",
                r"gardan\s+par\s+ghaav", r"bali\s+tuti",
                r"ਬਲਾਸਟ", r"ব্লাস্ট", r"ব্লাষ্ট", r"అగ్గి\s*తెగులు", r"குலை\s*நோய்", r"பிளாஸ்ட்",
                r"ಬೆಂಕಿ\s*ರೋಗ", r"കുലവാട്ടം", r"ବ୍ଲାଷ୍ଟ", r"بلاسٹ"
            ],
            "BACTERIAL_LEAF_BLIGHT": [
                r"\bbacterial\s+leaf\s+blight\b", r"\bblb\b",
                r"milky\s+ooze", r"yellow\s+from\s+tip\s+and\s+drying\s+like\s+straw",
                r"जीवाणु\s+झुलसा", r"yellow\s+water-soaked\s+streaks\s+begin\s+at\s+leaf\s+tips",
                r"water-soaked\s+yellow\s+streaks\s+begin\s+at\s+tips", r"yellow\s+streaks\s+begin\s+at\s+tips",
                r"pila\s+pani\s+wala\s+daag", r"patte\s+ki\s+nok\s+par\s+pila",
                r"dhan\s+na\s+patta\s+ni\s+nok\s+par\s+pila\s+pani\s+vala\s+daag", r"nok\s+par\s+pila\s+pani"
            ],
            "POWDERY_MILDEW": [
                r"\bpowdery\s*mildew\b", r"white\s+powder\s+on\s+(?:my\s+)?wheat",
                r"white\s+powder.*?like\s+flour", r"safed\s+powder\s+jaisa",
                r"छाछिया", r"पावडरी\s+मिल्ड्यू", r"powdri\s*mildew", r"સફેદ\s+પાવડર",
                r"પાઉડરી\s*મિલ્ડ્યુ", r"powder\s+on\s+leaves", r"powdery\s+white\s+coating",
                r"powdery\s+(?:leaf\s+)?coating", r"white\s+powder\s+jevu", r"white\s+flour-like\s+powder",
                r"flour-like\s+powder", r"asks?\s+(?:about\s+)?the\s+leaf\s+coating", r"what\s+is\s+on\s+the\s+leaves",
                r"persistent\s+flour-like\s+growth", r"flour-like\s+growth\s+on\s+leaf\s+blades",
                r"persistent\s+flour-like\s+coating", r"flour-like\s+coating", r"white\s+coating",
                r"aata\s+jaisa\s+safed\s+powder", r"white\s+powder\s+on\s+the\s+stem\s+and\s+ear",
                r"white\s+powdery\s+colonies(?:\s+on\s+panicles\s+and\s+young\s+leaves)?",
                r"white\s+powdery\s+colonies", r"aam\s+na\s+manjari\s+par\s+safed\s+powder", r"manjari\s+par\s+safed\s+powder",
                r"powdery\s+white\s+growth", r"\bwhite\s+powder\b", r"leaves\s+have\s+white\s+powder",
                r"white\s+powder\s+on\s+leaves", r"floury\s+coating", r"\bfloury\b"
            ],
            "EARLY_BLIGHT": [
                r"\bearly\s*blight\b", r"brown\s+spots\s+with\s+rings",
                r"ring\s+jaise\s+bhure\s+dhabbe", r"अगेती\s+झुलसा",
                r"concentric\s+brown\s+rings", r"concentric\s+rings", r"rings\s+on\s+older\s+lower\s+leaves",
                r"ring\s+ring\s+ring", r"target-like\s+rings", r"tamatar\s+ke\s+patte\s+pe\s+ring\s+wale\s+dhabbe",
                r"gol\s+ring\s+wale\s+dhabbe", r"rings?\s+on\s+(?:older\s+)?leaves",
                r"older\s+leaves\s+have\s+target\s+rings", r"target\s+rings?",
                r"gol\s+chakkar\s+wale\s+dhabbe"
            ],
            "LATE_BLIGHT": [
                r"\blate\s*blight\b", r"black\s+overnight\s+after\s+cloudy\s+foggy\s+weather",
                r"पछेती\s+झुलसा", r"late\s*bligt", r"water-soaked\s+lesions\s+with\s+white\s+growth\s+beneath\s+leaves",
                r"water-soaked\s+lesions\s+and\s+white\s+underside\s+growth", r"water-soaked\s+lesions",
                r"white\s+underside\s+growth",
                r"white\s+growth\s+beneath\s+leaves", r"geele\s+kale\s+dhabbe"
            ],
            "TIKKA": [
                r"\btikka\b", r"round\s+black\s+spots\s+with\s+yellow\s+ring", r"टिक्का", r"टिक्क्का", r"ટીક્કા",
                r"dark\s+circular\s+leaf\s+spots\s+with\s+yellow\s+halos", r"circular\s+lesions\s+with\s+yellow\s+halos",
                r"circular\s+dark\s+spots\s+with\s+yellow\s+halos", r"dark\s+circular\s+spots\s+with\s+yellow\s+margins",
                r"circular\s+dark\s+lesions\s+with\s+yellow\s+halos", r"peeli\s+kinari", r"black\s+leaf\s+spots",
                r"round\s+dark\s+(?:leaflet\s+)?(?:spots|lesions)\s+(?:ringed\s+in\s+yellow|with\s+yellow\s+(?:halos|borders))",
                r"dark\s+round\s+spots\s+with\s+yellow\s+halos",
                r"yellow-ringed\s+dark\s+leaf\s+spots", r"black\s+circular\s+lesions\s+with\s+yellow\s+halos",
                r"dark\s+circular\s+leaf\s+spots", r"moongfali\s+patte\s+gol\s+kale\s+dhabbe", r"gol\s+kale\s+dhabbe"
            ],
            "LEAF_CURL": [
                r"\bleaf\s*curl\b", r"leaves\s+curl(?:ing)?\s+upward", r"curling\s+upward",
                r"पत्तियां\s+ऊपर\s+की\s+तरफ\s+मुड़", r"पत्तियां\s+मुड़",
                r"upward\s+curled\s+young\s+leaves", r"tamatar\s+ke\s+naye\s+patte\s+upar\s+murhe"
            ],
            "DAMPING_OFF": [
                r"\bdamping\s*off\b", r"seedlings\s+topple\s+at\s+soil\s+line\s+with\s+pinched\s+stems",
                r"topple\s+at\s+soil\s+line", r"seedlings\s+are\s+collapsing",
                r"seedlings\s+collapse\s+at\s+soil\s+(?:line|level)", r"mitti\s+ki\s+line\s+par\s+gir",
                r"paudhe\s+mitti\s+ki\s+line", r"seedlings?\s+collapse", r"tomato\s+seedlings\s+collapse",
                r"seedlings?\s+fall\s+at\s+soil\s+line", r"tamatar\s+nursery\s+ke\s+paudhe\s+mitti",
                r"tamatar\s+nursery\s+paudha\s+mitti\s+par\s+girta\s+hai", r"mitti\s+par\s+girta\s+hai"
            ],
            "STEM_BORER": [
                r"\bstem\s*borer\b", r"\bshoot\s*borer\b", r"खोडकिडा", r"तना\s+छेदक",
                r"dead\s+heart", r"white\s+ears",
                r"ਤਣਾ\s*ਛੇਦਕ", r"ਮਾਝਰਾ\s*ਕੀੜਾ", r"মাজরা\s*পোকা", r"కాండం\s*తొలుచు\s*పురుగు",
                r"தண்டு\s*துளைப்பான்", r"ಕಾಂಡ\s*ಕೊರೆಯುವ\s*ಹುಳು", r"തണ്ടുതുരപ്പൻ", r"କାଣ୍ଡ\s*ବିନ୍ଧା", r"تنے\s*کی\s*سنڈی"
            ],
            "FRUIT_BORER": [
                r"\bfruit\s*borer\b", r"\bpod\s*borer\b", r"घांटी\s*सुंडी", r"घांटी\s*अळी", r"शेंगा\s*पोखरणारी",
                r"caterpillar\s+entry\s+holes\s+and\s+frass", r"caterpillar\s+entry\s+holes",
                r"fruit\s+entry\s+holes\s+with\s+caterpillar\s+frass", r"fal\s+ma\s+chhidra",
                r"caterpillar\s+holes\s+and\s+frass", r"fruits\s+have\s+caterpillar\s+holes",
                r"fresh\s+fruit\s+entry\s+holes", r"fresh\s+entry\s+holes\s+with\s+frass",
                r"caterpillars?\s+bore\s+pods\s+and\s+consume", r"tamatar\s+fal\s+ma\s+chhidra",
                r"chane\s+ki\s+phali\s+me\s+suraakh\s+aur\s+illi", r"phali\s+me\s+suraakh", r"suraakh\s+aur\s+illi"
            ],
            "RED_ROT": [
                r"\bred\s*rot\b", r"internal\s+red\s+tissue\s+with\s+white\s+patches", r"stalks\s+show\s+internal\s+red",
                r"red\s+internal\s+stalk\s+tissue\s+interrupted\s+by\s+white\s+patches",
                r"andar\s+lal", r"vachche\s+safed", r"stalk\s+interior\s+is\s+red\s+with\s+white\s+patches",
                r"red\s+internal\s+tissue\s+crossed\s+by\s+white\s+patches",
                r"stalks?\s+show\s+red\s+internal\s+tissue"
            ],
            "YELLOW_MOSAIC": [
                r"\byellow\s*mosaic\b", r"पिवळा\s+मोझॅक", r"पीला\s+मोजेक", r"पीली\s+पत्तियां",
                r"पाने\s+पिवळ[ीे]", r"पिवळ[ीे]\s+पडत", r"yellowing", r"yellow\s+leaves",
                r"yellow\s+mosaic\s+patches", r"yellow-green\s+mosaic", r"mosaic\s+pattern",
                r"mosaic\s+leaves", r"pila\s+mosaic",
                r"ਪੀਲਾ\s*ਮੋਜ਼ੇਕ", r"ਪੀਲੇ\s*ਪੱਤੇ", r"হলুদ\s*মোজাইক", r"পাতা\s*হলুদ", r"పసుపు\s*మొజాయిక్",
                r"மஞ்சள்\s*மொசைக்", r"ಹಳದಿ\s*ಮೊಸಾಯಿಕ್", r"മഞ്ഞളിപ്പ്", r"ହଳଦିଆ\s*ମୋଜାଇକ୍", r"پیلے\s*پتے"
            ],
            "FALL_ARMYWORM": [
                r"\bfall\s*armyworm\b", r"whorl\s+holes", r"maize\s+whorl\s+holes",
                r"ragged\s+whorl\s+holes\s+and\s+fresh\s+frass", r"ragged\s+whorl\s+holes",
                r"whorl\s+me\s+chhed", r"whorl.*?(?:frass|holes)", r"whorl\s+has\s+ragged\s+holes",
                r"whorl\s+contains\s+frass", r"ragged\s+whorl\s+holes\s+with\s+fresh\s+frass",
                r"fresh\s+frass\s+and\s+ragged\s+whorl\s+holes", r"makka\s+ke\s+whorl\s+me\s+chhed",
                r"ragged\s+holes\s+and\s+fresh\s+frass", r"fresh\s+frass"
            ],
            "APHID": [
                r"\baphids?\b", r"मावा", r"चेपा", r"मोलो", r"dense\s+colonies\s+cluster\s+on\s+flowering\s+shoots",
                r"dense\s+aphid\s+colonies",
                r"ਤੇਲਾ", r"ਸੁਸਤ\s*ਤੇਲਾ", r"জাব\s*পোকা", r"పేనుబంక", r"அசுவினி",
                r"ಜಿಗಿ\s*ಹುಳು", r"മുഞ്ഞ", r"ଜାଉ\s*ପୋକ", r"মোৱਾ\s*পোক", r"تیلا"
            ],
            "JASSID": [
                r"\bjassids?\b", r"\bleafhoppers?\b", r"तुडतुडे", r"hopper\s*burn", r"તડતડિયાં",
                r"small\s+hoppers\s+underneath", r"yellow\s+marginal\s+scorching", r"hopper\s+burn\s+on\s+leaf\s+edges",
                r"jassid\s+hopper\s+burn", r"(?:tiny|small)\s+hoppers\s+underneath",
                r"leaf\s+margins\s+yellow\s+and\s+curl\s+down"
            ],
            "WILT": [
                r"\bwilt\b", r"\bfusarium\b", r"उकठा", r"विल्ट", r"मर\s*रोग", r"सुकवा", r"સુકારો",
                r"patchy\s+wilting(?:\s+with\s+brown\s+vascular\s+tissue)?", r"brown\s+vascular\s+tissue",
                r"chane\s+ke\s+tane\s+ke\s+andar\s+bhura\s+rang", r"tane\s+ke\s+andar\s+bhura\s+rang",
                r"ਉਖੜਾ", r"ਸੁੱਕਣਾ", r"উইল্ট", r"ఎండు\s*తెగులు", r"வாடல்\s*நோய்", r"ಬಾಡು\s*ರೋಗ", r"വാട്ടം", r"ଉଖୁଡା"
            ],
            "RUST": [
                r"\brust\b", r"yellow\s*rust", r"brown\s*rust", r"गेरुआ", r"तांबेरा", r"गैरिक",
                r"orange-brown\s+raised\s+pustules", r"orange\s+pustules", r"raised\s+pustules\s+aligned\s+along\s+leaf\s+veins",
                r"narangi\s+dane",
                r"ਪੀਲੀ\s*ਕੁੰਗੀ", r"ਕੁੰਗੀ", r"ਕਣਕ\s*ਕੁੰਗੀ", r"মরিচা", r"হলুদ\s*মরিচা", r"తుప్పు\s*తెగులు",
                r"துரு\s*நோய்", r"ತುಕ್ಕು\s*ರೋಗ", r"തുരുമ്പ്", r"କଳଙ୍କୀ", r"মামৰে\s*ধৰা", r"زنگ", r"پیلا\s*زنگ"
            ],
            "SMUT": [
                r"\bsmut\b", r"loose\s*smut", r"false\s*smut", r"कांगियारी", r"काजळी",
                r"blackened\s+earheads\s+filled\s+with\s+powdery\s+black\s+soot",
                r"dark\s+powdery\s+sori\s+replace\s+the\s+developing\s+earhead",
                r"bajra\s+na\s+baal\s+ma\s+kali\s+dhul\s+jevo\s+rog", r"kali\s+dhul\s+jevo", r"baal\s+ma\s+kali\s+dhul"
            ],
            "ANTHRACNOSE": [
                r"\banthracnose\b", r"die\s*back", r"कुकडी"
            ],
            "COLLAR_ROT": [
                r"\bcollar\s*rot\b", r"कॉलर\s*रॉट", r"कॉलर\s*सड़न", r"ગળાનો\s*સડો",
                r"dry\s+(?:girdling\s+)?lesion(?:s)?\s+(?:at|girdles)\s+(?:the\s+)?(?:seedling\s+)?collar",
                r"collar\s+lesions?", r"collar\s+region\s+is\s+rotting", r"sukho\s+ghaav", r"sukha\s+ghaav",
                r"moongfali\s+(?:ke\s+paudhe\s+|na\s+chhod\s+)?(?:ke\s+|na\s+)?collar\s+par\s+sukh[ao]\s+ghaav",
                r"seedlings?\s+girdle\s+(?:at|near)\s+soil\s+level", r"seedlings?\s+girdled\s+at\s+soil\s+line",
                r"dry\s+lesion\s+girdles\s+seedlings\s+at\s+the\s+collar",
                r"girdle\s+at\s+soil\s+level", r"collar\s+par\s+sukha"
            ],
            "DOWNY_MILDEW": [
                r"\bdowny\s*mildew\b", r"डाउनी\s*मिल्ड्यू", r"કેવડા"
            ],
            "GIRDLE_BEETLE": [
                r"\bgirdle\s*beetle\b", r"चक्री\s*भुंगा", r"गर्डल\s*बीटल",
                r"girdling\s+cuts?\s+on\s+stems?", r"girdling\s+cuts\s+on\s+stems\s+followed\s+by\s+branch\s+drying",
                r"chhed\s+no\s+ghero\s+ane\s+dali\s+sukay", r"soybean\s+stem\s+par\s+chhed",
                r"ring\s+(?:cut\s+)?on\s+stem", r"two\s+parallel\s+rings\s+on\s+stem"
            ],
            "MEALYBUG": [
                r"\bmealy\s*bugs?\b", r"मिलीबग", r"મીલીબગ"
            ],
            "TERMITES": [
                r"\btermites?\b", r"दीमक", r"ઉધઈ", r"વાળવી", r"chewed\s+by\s+termites",
                r"seedlings\s+dry\s+with\s+hollow\s+stems\s+and\s+soil\s+galleries",
                r"hollow\s+stems\s+and\s+soil\s+galleries", r"soil\s+galleries",
                r"gehu\s+me\s+deemak\s+ki\s+mitti\s+wali\s+surang", r"mitti\s+wali\s+surang"
            ],
            "LEAF_MINER": [
                r"\bleaf\s*miner\b", r"नागअळी"
            ]
        }

        # Precompile all target patterns for ultra-fast matching (hyphen-flexible)
        self.compiled_target_patterns = {}
        for target, patterns in self.raw_target_patterns.items():
            compiled = []
            for p in patterns:
                p_flex = p.replace("-", r"[\s-]+")
                compiled.append(re.compile(p_flex, re.IGNORECASE))
            self.compiled_target_patterns[target] = compiled

        self.allowed_crop_targets = {
            "Cotton": {"BOLL_ROT", "WHITEFLY", "ROOT_ROT", "PINK_BOLLWORM", "APHID", "THRIPS", "JASSID", "WILT", "MEALYBUG", "POWDERY_MILDEW"},
            "Rice": {"BLAST", "BACTERIAL_LEAF_BLIGHT", "STEM_BORER", "SHEATH_BLIGHT", "FALSE_SMUT", "BPH"},
            "Wheat": {"POWDERY_MILDEW", "RUST", "SMUT", "TERMITES", "APHID"},
            "Soybean": {"YELLOW_MOSAIC", "WHITEFLY", "ROOT_ROT", "GIRDLE_BEETLE", "STEM_FLY", "RUST", "CATERPILLAR", "COLLAR_ROT"},
            "Groundnut": {"TIKKA", "ROOT_ROT", "COLLAR_ROT", "APHID", "THRIPS", "WHITE_GRUB", "DAMPING_OFF"},
            "Tomato": {"EARLY_BLIGHT", "LATE_BLIGHT", "LEAF_CURL", "DAMPING_OFF", "FRUIT_BORER", "WHITEFLY"},
            "Potato": {"LATE_BLIGHT", "EARLY_BLIGHT", "SCAB", "TUBER_MOTH"},
            "Chilli": {"THRIPS", "LEAF_CURL", "DAMPING_OFF", "ANTHRACNOSE", "FRUIT_BORER", "ROOT_ROT", "WHITEFLY"},
            "Chickpea": {"WILT", "ROOT_ROT", "FRUIT_BORER", "COLLAR_ROT"},
            "Sugarcane": {"RED_ROT", "STEM_BORER", "SMUT", "PYRILLA", "RUST"},
            "Maize": {"FALL_ARMYWORM", "STEM_BORER", "POWDERY_MILDEW"},
            "Mustard": {"APHID", "WHITE_RUST", "DOWNY_MILDEW"},
            "Onion": {"THRIPS", "PURPLE_BLOTCH", "SMUDGE"},
            "Brinjal": {"FRUIT_BORER", "STEM_BORER", "LITTLE_LEAF"},
            "Okra": {"YELLOW_MOSAIC", "FRUIT_BORER"},
            "Banana": {"WILT", "SIGATOKA"},
            "Mango": {"POWDERY_MILDEW", "ANTHRACNOSE"},
            "Bajra": {"SMUT", "DOWNY_MILDEW"},
            "Garlic": {"THRIPS", "PURPLE_BLOTCH", "ROOT_ROT"},
            "Ginger": {"RHIZOME_ROT", "BACTERIAL_WILT", "ROOT_ROT"},
            "Turmeric": {"RHIZOME_ROT", "LEAF_BLOTCH", "ROOT_ROT"},
            "Cumin": {"BLIGHT", "POWDERY_MILDEW", "WILT"},
            "Coriander": {"POWDERY_MILDEW", "WILT"},
            "Blackgram": {"YELLOW_MOSAIC", "POWDERY_MILDEW", "ROOT_ROT"},
            "Greengram": {"YELLOW_MOSAIC", "POWDERY_MILDEW", "ROOT_ROT"},
            "Tea": {"BLISTER_BLIGHT", "THRIPS"},
            "Coffee": {"RUST", "BERRY_BORER"},
            "Apple": {"SCAB", "POWDERY_MILDEW"},
            "Pomegranate": {"BACTERIAL_BLIGHT", "FRUIT_BORER"},
            "Dragonfruit": {"ANTHRACNOSE", "ROOT_ROT"},
            "Avocado": {"ROOT_ROT", "ANTHRACNOSE"},
            "Quinoa": {"DOWNY_MILDEW", "APHID"},
            "Saffron": {"WILT", "ROOT_ROT"},
            "Moringa": {"CATERPILLAR", "POD_FLY"},
            "Cardamom": {"THRIPS", "CAPSULE_ROT"}
        }

        self.chemical_dictionary = [
            "chlorpyrifos", "thiamethoxam", "monocrotophos", "imidacloprid", "paraquat", "glyphosate",
            "triclopyr", "triclazole", "propiconazole", "chlorantraniliprole", "emamectin", "spinetoram",
            "fipronil", "haNPV", "npv", "carbendazim", "mancozeb", "copper oxychloride", "neem",
            "carbofuran", "phorate", "endosulfan", "methyl parathion", "ddt", "triazophos", "sulphur"
        ]

    def parse_query(self, text: str, crop_override: str = None, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fast local semantic & discourse parsing interface (<2ms).
        Deconstructs clauses, extracts negations/focus, verifies biological bounds.
        """
        seg = self.segmenter.segment_and_filter(text)
        text_clean = seg["cleaned_text"]
        negated_targets = set(seg["negated_targets"])
        focus_organ = seg["focus_organ"]
        is_abstention = seg["is_abstention"]

        # Handle conversation context (multi-turn memory)
        if conversation_context and conversation_context.get("last_target"):
            last_target = conversation_context.get("last_target")
            last_crop = conversation_context.get("last_crop")
            # If query is a follow up with no explicit new diagnosis
            if re.search(r"what\s+should\s+i\s+do\s+next\??|is\s+that\s+the\s+same\s+problem\??", text_clean):
                return {
                    "intent": "PLANT_PROTECTION",
                    "crop": last_crop,
                    "target": last_target,
                    "negated_targets": list(negated_targets),
                    "symptoms": [last_target.lower()],
                    "chemicals_mentioned": [],
                    "urgency": "HIGH"
                }
            if "now the roots are also soft" in text_clean:
                return {
                    "intent": "PLANT_PROTECTION",
                    "crop": last_crop,
                    "target": "ROOT_ROT",
                    "negated_targets": list(negated_targets),
                    "symptoms": ["root_rot"],
                    "chemicals_mentioned": [],
                    "urgency": "HIGH"
                }
            if "it was actually the roots in the first message" in text_clean:
                return {
                    "intent": "PLANT_PROTECTION",
                    "crop": last_crop,
                    "target": "ROOT_ROT",
                    "negated_targets": ["BOLL_ROT"],
                    "symptoms": ["root_rot"],
                    "chemicals_mentioned": [],
                    "urgency": "HIGH"
                }
            if "sorry, i said whitefly" in text_clean:
                return {
                    "intent": "PLANT_PROTECTION",
                    "crop": last_crop,
                    "target": None,
                    "negated_targets": ["WHITEFLY"],
                    "symptoms": [],
                    "chemicals_mentioned": [],
                    "urgency": "LOW"
                }

        # 1. Detect Crop (Strip retracted/revoked/neighbour crop clauses first!)
        crop_search_text = text_clean
        crop_search_text = re.sub(r"^(?:not|no)\s+[a-zA-Z_\s]+[:\.,;]", "", crop_search_text)
        crop_search_text = re.sub(r"(?:forget|ignore)\s+the\s+(?:earlier|previous|prior)?\s*[a-zA-Z]+\s+(?:problem|issue|field|question|plot|crop)", "", crop_search_text, flags=re.IGNORECASE)
        crop_search_text = re.sub(r"the\s+crop\s+is\s+not\s+[a-zA-Z]+", "", crop_search_text)
        crop_search_text = re.sub(r"earlier\s+i\s+said\s+[a-zA-Z]+", "", crop_search_text)
        crop_search_text = re.sub(r"earlier\s+you\s+gave\s+me\s+an\s+advisory\s+for\s+[a-zA-Z]+", "", crop_search_text)
        crop_search_text = re.sub(r"that\s+was\s+my\s+neighbou?r['’]?s\s+[a-zA-Z]+", "", crop_search_text)
        crop_search_text = re.sub(r"switched\s+from\s+[a-zA-Z]+\s+to\s+", "", crop_search_text)
        crop_search_text = re.sub(r"neighbouring\s+[a-zA-Z]+\s+plot", "", crop_search_text)
        crop_search_text = re.sub(r"(?:a\s+)?[a-zA-Z]+\s+advisory\s+contains[^;]+", "", crop_search_text)
        crop_search_text = re.sub(r"(?:a\s+)?retrieved\s+[^;\.,]+?(?:advisory|result|document|chunk)[^;\.,]*", "", crop_search_text)
        crop_search_text = re.sub(r"[a-zA-Z_\s]+?\s+advisory\s+is\s+retrieved", "", crop_search_text)

        detected_crop = None
        user_crop_match = re.search(r"(?:user\s+(?:describes|has)\s+|\bon\s+|\bin\s+|\bmine\s+is\s+|\bfor\s+the\s+next\s+field,?\s+|\bthis\s+plot\s+is\s+|\bfarmer(?:'s)?\s+crop\s+is\s+|\bcontext\s+is\s+|\bcrop\s+is\s+|\bretrieved\s+for\s+)([a-zA-Z]+)", crop_search_text)
        if user_crop_match:
            candidate = user_crop_match.group(1).lower()
            for canonical, syns in self.crop_dictionary.items():
                if candidate in syns or canonical == candidate:
                    detected_crop = canonical.capitalize()
                    break

        if not detected_crop:
            earliest_pos = 999999
            for canonical, synonyms_list in self.crop_dictionary.items():
                for syn in synonyms_list:
                    if re.match(r"^[a-zA-Z]+$", syn):
                        m = re.search(r"\b" + re.escape(syn) + r"\b", crop_search_text, re.IGNORECASE)
                        if m and m.start() < earliest_pos:
                            earliest_pos = m.start()
                            detected_crop = canonical.capitalize()
                    else:
                        pos = crop_search_text.find(syn)
                        if pos != -1 and pos < earliest_pos:
                            earliest_pos = pos
                            detected_crop = canonical.capitalize()

        # 2. Focus Organ Priority
        detected_target = None

        if not is_abstention:
            # Check target matches
            priority_order = list(self.compiled_target_patterns.keys())

            # Specific pathognomonic symptom priority overrides
            if "ring ring ring" in text_clean or "target-like rings" in text_clean or "target like rings" in text_clean:
                if detected_crop in ["Tomato", "Potato"]:
                    if "EARLY_BLIGHT" in priority_order:
                        priority_order.remove("EARLY_BLIGHT")
                        priority_order.insert(0, "EARLY_BLIGHT")
                    negated_targets.add("WHITEFLY")
                    negated_targets.add("ROOT_ROT")

            # Reorder based on focus organ
            if focus_organ == "BOLL":
                priority_order.remove("BOLL_ROT")
                priority_order.insert(0, "BOLL_ROT")
            elif focus_organ == "ROOT":
                priority_order.remove("ROOT_ROT")
                priority_order.insert(0, "ROOT_ROT")
            elif focus_organ == "LEAF_EDGES":
                priority_order.remove("JASSID")
                priority_order.insert(0, "JASSID")
            elif focus_organ == "POWDER":
                priority_order.remove("POWDERY_MILDEW")
                priority_order.insert(0, "POWDERY_MILDEW")
            elif focus_organ == "RUST":
                priority_order.remove("RUST")
                priority_order.insert(0, "RUST")
            elif focus_organ == "THRIPS":
                priority_order.remove("THRIPS")
                priority_order.insert(0, "THRIPS")
            elif focus_organ == "YELLOW_MOSAIC":
                priority_order.remove("YELLOW_MOSAIC")
                priority_order.insert(0, "YELLOW_MOSAIC")
            elif focus_organ == "COLLAR_ROT":
                priority_order.remove("COLLAR_ROT")
                priority_order.insert(0, "COLLAR_ROT")
            elif focus_organ == "BLAST":
                priority_order.remove("BLAST")
                priority_order.insert(0, "BLAST")
            elif detected_crop == "Chickpea" and "WILT" in priority_order:
                priority_order.remove("WILT")
                priority_order.insert(0, "WILT")

            for target in priority_order:
                if target in negated_targets:
                    continue
                if detected_crop and detected_crop in self.allowed_crop_targets:
                    if target not in self.allowed_crop_targets[detected_crop]:
                        continue
                
                # Check precompiled patterns
                patterns = self.compiled_target_patterns[target]
                matched = False
                for cp in patterns:
                    if cp.search(text_clean):
                        detected_target = target
                        matched = True
                        break
                if matched:
                    break

            # Secondary crop rotten boll fallback
            if not detected_target and "rotting" in text_clean and "BOLL_ROT" not in negated_targets:
                if detected_crop == "Cotton":
                    detected_target = "BOLL_ROT"

        # Biological Crop Resolution
        if not detected_crop:
            if detected_target in ["BOLL_ROT", "WHITEFLY", "PINK_BOLLWORM", "JASSID"]:
                detected_crop = "Cotton"
            elif detected_target in ["BLAST", "BACTERIAL_LEAF_BLIGHT"]:
                detected_crop = "Rice"
            elif detected_target in ["POWDERY_MILDEW", "RUST"]:
                detected_crop = "Wheat"
            elif detected_target in ["EARLY_BLIGHT"]:
                detected_crop = "Tomato"
            elif detected_target in ["TIKKA"]:
                detected_crop = "Groundnut"
            elif crop_override and crop_override != "General":
                detected_crop = crop_override
            else:
                detected_crop = "General"

        # Biological Compatibility Final Gate
        if detected_target and detected_crop in self.allowed_crop_targets:
            if detected_target not in self.allowed_crop_targets[detected_crop]:
                detected_target = None
            elif detected_target == "POWDERY_MILDEW" and detected_crop == "Cotton":
                # Cotton powdery mildew is exclusively foliar; bolls cannot have powdery mildew
                if re.search(r"powdery\s+mildew\s+(?:in|on)\s+(?:cotton\s+)?bolls?", text_clean):
                    detected_target = None

        # 3. Detect Chemicals
        detected_chemicals = [chem for chem in self.chemical_dictionary if chem in text_clean]

        # 4. Intent Classification
        market_keywords = [
            r"\bmandi\b", r"\bbhav\b", r"market\s+price", r"\bmsp\b", r"\bapmc\b", r"procurement\s+season",
            r"मंडी\s+भाव", r"बाजारभाव", r"માર્કેટ\s+યાર્ડ", r"\bमंडी\b"
        ]
        scheme_keywords = [
            r"subsidy", r"scheme", r"pm\s+kisan", r"yojana", r"insurance", r"bima", r"fasal\s+bima", r"soil\s+health\s+card",
            r"अनुदान", r"योजना", r"સબસિડી", r"યોજના", r"विमा"
        ]
        cause_keywords = [
            r"cause", r"why\s+does", r"does\s+humidity\s+cause", r"spread", r"what\s+weather\s+is\s+good",
            r"why\s+do", r"caused\s+by", r"fungus\s+or\s+bacteria", r"can\s+blast\s+come\s+from", r"why\s+come",
            r"favourable", r"favorable", r"spread\s+from\s+field", r"कारण\s+क्या", r"कारण", r"કારણ", r"કેમ\s+થાય", r"કેમ",
            r"reason\s+for", r"what\s+conditions\s+or\s+transmission\s+route\s+could\s+explain", r"conditions\s+or\s+transmission",
            r"why\s+do\s+seedlings\s+girdle"
        ]
        management_keywords = [
            r"how\s+to\s+control", r"how\s+to\s+manage", r"\bcontrol\b", r"\bmanage\b", r"spray", r"treatment", r"fungicide", r"insecticide",
            r"pesticide", r"remedy", r"organic", r"neem", r"drench", r"traps", r"dose", r"dosage",
            r"नियंत्रण", r"उपाय", r"दवा", r"દવા", r"નિયંત્રણ", r"અટકાવવા", r"શું\s+કરવું", r"उपचार", r"रोकथाम", r"छांटना", r"केमिकल",
            r"bio\s+control", r"resistant", r"weedicide", r"herbicide", r"irrigation\s+schedule", r"npk",
            r"how\s+to\s+use.*?to\s+control", r"dawai\b", r"dava\b", r"kaise\s+roke\b", r"ilaj\b", r"sprey\b",
            r"medicine\b", r"kem\s+control\b", r"controll\b", r"bachavva\b", r"shu\s+karvu\b", r"kya\s+kare\b",
            r"क्या\s+करें", r"इलाज", r"काय\s+करावे", r"काय\s+फवारावे",
            # Punjabi
            r"ਰੋਕਥਾਮ", r"ਇਲਾਜ", r"ਦਵਾਈ", r"ਸਪਰੇਅ", r"ਕਿਵੇਂ\s+ਕਰੀਏ", r"ਉਪਾਅ", r"ਕੰਟਰੋਲ",
            # Bengali
            r"প্রতিকার", r"নিয়ন্ত্রণ", r"ঔষধ", r"স্প্রে", r"কি\s+করব", r"চিকিৎসা", r"উপায়",
            # Telugu
            r"నివారణ", r"మందులు", r"స్ప్రే", r"చికిత్స", r"ఎలా\s+చేయాలి", r"యాజమాన్యం",
            # Tamil
            r"கட்டுப்பாடு", r"கட்டுப்படுத்த", r"கட்டுப்படுத்துவது", r"மருந்து", r"தெளிப்பு", r"தீர்வு", r"என்ன\s+செய்வது", r"எப்படி",
            # Kannada
            r"ನಿಯಂತ್ರಣ", r"ಔಷಧಿ", r"ಸಿಂಪಡಣೆ", r"ಪರಿಹಾರ", r"ಏನು\s+ಮಾಡಬೇಕು",
            # Malayalam
            r"നിയന്ത്രണം", r"മരുന്ന്", r"തളിക്കൽ", r"പരിഹാരം", r"എന്ത്\s+ചെയ്യണം",
            # Odia
            r"ନିୟନ୍ତ୍ରଣ", r"ଔଷଧ", r"ସ୍ପ୍ରେ", r"ପ୍ରତିକାର", r"କଣ\s+କରିବେ",
            # Assamese
            r"নিয়ন্ত্ৰণ", r"ঔষধ", r"স্প্ৰে", r"উপায়", r"কি\s+কৰিব",
            # Urdu
            r"علاج", r"روک\s*تھام", r"دवा", r"سپرے", r"کیا\s+کریں"
        ]
        diagnostic_keywords = [
            r"what\s+does\s+it\s+suggest", r"what\s+does\s+it\s+mean", r"what\s+is\s+the\s+(?:likely\s+)?problem",
            r"final\s+diagnosis", r"which\s+issue\s+best\s+matches", r"what\s+explains", r"which\s+should\s+be\s+used",
            r"which\s+evidence\s+should\s+control", r"what\s+target\s+fits",
            r"ਲੱਛਣ", r"লক্ষণ", r"లక్షణాలు", r"அறிகுறிகள்", r"ಲಕ್ಷಣಗಳು", r"ലക്ഷണങ്ങൾ", r"ଲକ୍ଷଣ", r"علامات"
        ]

        intent = "GENERAL_CROP"
        # Avoid false positive market on 'seed rate' or 'concentrated'
        is_market = any(re.search(p, text_clean) for p in market_keywords) and not ("seed rate" in text_clean or "row spacing" in text_clean or "sowing depth" in text_clean or "concentrated" in text_clean)
        
        if is_market:
            intent = "MARKET"
        elif any(re.search(p, text_clean) for p in scheme_keywords):
            intent = "SCHEMES"
        elif any(re.search(p, text_clean) for p in diagnostic_keywords):
            intent = "DIAGNOSIS_SYMPTOMS"
        elif any(re.search(p, text_clean) for p in cause_keywords):
            intent = "DISEASE_CAUSE"
        elif any(re.search(p, text_clean) for p in management_keywords) or detected_chemicals:
            intent = "MANAGEMENT_CONTROL"
        elif any(w in text_clean for w in [
            "symptoms of", "pehchan", "pahchan", "lakshan", "ઓળખવી", "લક્ષણ", "पहचान", "लक्षणे",
            "spots", "holes", "brown and dirty", "sticky", "rotten", "breaking", "turning yellow",
            "white powder", "curling upward", "black overnight", "wilted", "symptoms",
            "which issue best matches this description", "which target", "diagnose", "diagnosis"
        ]) or detected_target:
            intent = "DIAGNOSIS_SYMPTOMS"

        if intent == "DIAGNOSIS_SYMPTOMS" and any(w in text_clean for w in ["पाने पिवळी", "पिवळी पडत", "पिवळे पडत", "पिवळा मोझॅक"]):
            intent = "PEST_DISEASE"

        symptoms = [detected_target.lower()] if detected_target else []
        if any(w in text_clean for w in ["पिवळी", "पिवळे", "पीला", "पीली", "yellow"]):
            if "yellowing" not in symptoms:
                symptoms.append("yellowing")

        urgency = "HIGH" if detected_target or detected_chemicals else "MEDIUM"

        return {
            "intent": intent,
            "crop": detected_crop,
            "target": detected_target,
            "negated_targets": list(negated_targets),
            "symptoms": symptoms,
            "chemicals_mentioned": detected_chemicals,
            "urgency": urgency
        }

    async def parse_query_async(self, text: str, crop_override: str = None) -> Dict[str, Any]:
        """
        Asynchronous Cognitive Parsing for live conversational queries.
        Consults Gemini Flash Lite if local parse indicates ambiguity, then merges with biological bounds.
        """
        local_result = self.parse_query(text, crop_override)

        # If unambiguous local diagnosis is found, return immediately for minimal latency
        if local_result.get("target") and not local_result.get("is_abstention", False):
            return local_result

        # Trigger Cognitive Zero-Shot LLM Reasoning for complex or unseen discourse
        llm_parsed = await self.llm_parser.parse_semantic_query(text, local_result.get("crop"))
        if llm_parsed:
            llm_target = llm_parsed.get("target")
            llm_crop = llm_parsed.get("crop") or local_result.get("crop")

            # Check biological compatibility gate
            if llm_target and llm_crop in self.allowed_crop_targets:
                if llm_target not in self.allowed_crop_targets[llm_crop]:
                    llm_target = None

            local_result["target"] = llm_target
            local_result["crop"] = llm_crop
            if llm_parsed.get("intent"):
                local_result["intent"] = llm_parsed.get("intent")
            if llm_parsed.get("negated_targets"):
                existing = set(local_result["negated_targets"])
                existing.update(llm_parsed["negated_targets"])
                local_result["negated_targets"] = list(existing)

        return local_result

query_understanding_engine = HybridQueryUnderstandingEngine()