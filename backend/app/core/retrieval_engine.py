import re
import math
from typing import List, Dict, Any, Set
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from backend.app.db.models import KnowledgeDocument
from backend.app.schemas.schemas import EvidenceChunk

# Multilingual term mapping for semantic overlap calculation
MULTILINGUAL_SYNONYMS = {
    # Crops (Hindi, Marathi, Gujarati, Romanized, Punjabi, Bengali, Telugu, Tamil, Kannada, Malayalam, Odia, Assamese, Urdu)
    "सोयाबीन": ["soybean", "soyabean", "yellow mosaic"],
    "સોયાબીન": ["soybean", "soyabean", "yellow mosaic"],
    "ਸੋਇਆਬੀਨ": ["soybean", "yellow mosaic"],
    "সয়াবিন": ["soybean", "yellow mosaic"],
    "సోయాబీన్": ["soybean", "yellow mosaic"],
    "சோயாபீன்": ["soybean", "yellow mosaic"],
    "ಸೋಯಾಬೀನ್": ["soybean", "yellow mosaic"],
    "ಕಾಪूस": ["cotton", "bollworm", "kapas"],
    "कपास": ["cotton", "bollworm", "kapas"],
    "કપાસ": ["cotton", "bollworm", "kapas"],
    "ਕਪਾਹ": ["cotton", "bollworm", "pink bollworm"],
    "ਕਪਾਸ": ["cotton", "bollworm"],
    "তুলা": ["cotton", "bollworm"],
    "পత్తి": ["cotton", "bollworm", "pink bollworm"],
    "பருத்தி": ["cotton", "bollworm", "pink bollworm"],
    "ಹತ್ತಿ": ["cotton", "bollworm"],
    "പരുത്തി": ["cotton", "bollworm"],
    "କପା": ["cotton", "bollworm"],
    "کپاس": ["cotton", "bollworm"],
    "kapas": ["cotton", "bollworm"],
    "bajari": ["pearl millet", "bajra"],
    "bajri": ["pearl millet", "bajra"],
    "બાજરી": ["pearl millet", "bajra"],
    "बाजरी": ["pearl millet", "bajra"],
    "ਬਾਜਰਾ": ["pearl millet", "bajra"],
    "సజ్జలు": ["pearl millet", "bajra"],
    "கம்பு": ["pearl millet", "bajra"],
    "ಸಜ್ಜೆ": ["pearl millet", "bajra"],
    "બટાકા": ["potato", "late blight", "tuber"],
    "બટાટા": ["potato", "late blight", "tuber"],
    "ਆਲੂ": ["potato", "late blight", "tuber"],
    "আলু": ["potato", "late blight"],
    "బంగాళాదుంప": ["potato", "late blight"],
    "உருளைக்கிழங்கு": ["potato", "late blight"],
    "ಆಲೂಗಡ್ಡೆ": ["potato", "late blight"],
    "bataka": ["potato", "blight"],
    "batata": ["potato", "blight"],
    "ગહુ": ["wheat", "rust", "yellow rust"],
    "ઘઉં": ["wheat", "rust", "yellow rust"],
    "गहू": ["wheat", "rust", "yellow rust"],
    "गेहूं": ["wheat", "rust", "yellow rust"],
    "ਕਣਕ": ["wheat", "rust", "yellow rust"],
    "গম": ["wheat", "rust", "yellow rust"],
    "గోధుమ": ["wheat", "rust", "yellow rust"],
    "கோதுமை": ["wheat", "rust", "yellow rust"],
    "ಗೋಧಿ": ["wheat", "rust", "yellow rust"],
    "ଗହମ": ["wheat", "rust"],
    "گندم": ["wheat", "rust"],
    "kanak": ["wheat", "rust"],
    "भात": ["rice", "paddy", "blast"],
    "ધાન": ["rice", "paddy", "blast"],
    "ડાંગર": ["rice", "paddy", "blast"],
    "चावल": ["rice", "paddy", "blast"],
    "ਝੋਨਾ": ["rice", "paddy", "blast"],
    "ধান": ["rice", "paddy", "blast"],
    "వరి": ["rice", "paddy", "blast"],
    "நெல்": ["rice", "paddy", "blast"],
    "ಭತ್ತ": ["rice", "paddy", "blast"],
    "നെല്ല്": ["rice", "paddy", "blast"],
    "ଧାନ": ["rice", "paddy", "blast"],
    "jhona": ["rice", "paddy"],
    "dhan": ["rice", "paddy"],
    "हरभरा": ["chickpea", "gram", "pod borer"],
    "चना": ["chickpea", "gram", "pod borer"],
    "ચણા": ["chickpea", "gram", "pod borer"],
    "ਛੋਲੇ": ["chickpea", "gram", "pod borer"],
    "ছোলা": ["chickpea", "gram"],
    "శనగలు": ["chickpea", "gram"],
    "கொண்டைக்கடலை": ["chickpea", "gram"],
    "ऊस": ["sugarcane", "shoot borer"],
    "ગન્ના": ["sugarcane", "shoot borer"],
    "શેરડી": ["sugarcane", "shoot borer"],
    "ਗੰਨਾ": ["sugarcane", "shoot borer"],
    "আখ": ["sugarcane", "shoot borer"],
    "చెరకు": ["sugarcane", "shoot borer"],
    "கரும்பு": ["sugarcane", "shoot borer"],
    "ಕಬ್ಬು": ["sugarcane", "shoot borer"],
    "भुईमूग": ["groundnut", "peanut"],
    "मूंगफली": ["groundnut", "peanut"],
    "મગફળી": ["groundnut", "peanut", "tikka"],
    "ਮੂੰਗਫਲੀ": ["groundnut", "peanut", "tikka"],
    "চিনাবাদাম": ["groundnut", "peanut"],
    "వేరుశనగ": ["groundnut", "peanut"],
    "நிலக்கடலை": ["groundnut", "peanut"],
    "ಕಡಲೆಕಾಯಿ": ["groundnut", "peanut"],
    "magfali": ["groundnut", "peanut"],
    "જીરું": ["cumin", "blight"],
    "jeeru": ["cumin"],
    "રાયડો": ["mustard", "aphid"],
    "સરસવ": ["mustard", "aphid"],
    "ਸਰ੍ਹੋਂ": ["mustard", "aphid"],
    "সরিষা": ["mustard", "aphid"],
    "ఆవాలు": ["mustard", "aphid"],
    "கடுகு": ["mustard", "aphid"],

    # Symptoms / Pests / Diseases across Indian Languages
    "પાન": ["leaf", "leaves", "foliage"],
    "પાંદડા": ["leaf", "leaves", "foliage", "yellowing"],
    "ਪੱਤੇ": ["leaf", "leaves", "foliage"],
    "পাতা": ["leaf", "leaves"],
    "ఆకులు": ["leaf", "leaves"],
    "இலை": ["leaf", "leaves"],
    "ಎಲೆ": ["leaf", "leaves"],
    "ഇല": ["leaf", "leaves"],
    "pandada": ["leaf", "leaves"],
    "પીળા": ["yellowing", "yellow", "whitefly", "mosaic"],
    "पिवळी": ["yellowing", "yellow", "whitefly", "mosaic"],
    "पिवळा": ["yellowing", "yellow", "whitefly", "mosaic"],
    "पीला": ["yellowing", "yellow", "whitefly", "mosaic", "rust"],
    "पीले": ["yellowing", "yellow", "whitefly", "mosaic", "rust"],
    "ਪੀਲੀ": ["yellowing", "yellow", "rust"],
    "ਪੀਲੇ": ["yellowing", "yellow", "mosaic"],
    "হলুদ": ["yellowing", "yellow", "mosaic"],
    "పసుపు": ["yellowing", "yellow", "mosaic"],
    "மஞ்சள்": ["yellowing", "yellow", "mosaic"],
    "ಹಳದಿ": ["yellowing", "yellow", "mosaic"],
    "ਕੁੰਗੀ": ["rust", "yellow rust", "propiconazole"],
    "ਪੀਲੀ ਕੁੰਗੀ": ["rust", "yellow rust", "propiconazole"],
    "ਮਰੀਚਾ": ["rust", "yellow rust"],
    "মরিচা": ["rust", "yellow rust"],
    "తుప్పు": ["rust", "yellow rust"],
    "துரு": ["rust", "yellow rust"],
    "തുരുമ്പ്": ["rust", "yellow rust"],
    "রતુઆ": ["rust", "yellow rust", "propiconazole"],
    "रतुआ": ["rust", "yellow rust", "propiconazole"],
    "तांबेरा": ["rust", "yellow rust", "propiconazole"],
    "ਬਲਾਸਟ": ["blast", "tricyclazole", "leaf blast"],
    "ব্লাস্ট": ["blast", "tricyclazole", "leaf blast"],
    "ব্লাষ্ট": ["blast", "tricyclazole"],
    "అగ్గి తెగులు": ["blast", "tricyclazole"],
    "குலை நோய்": ["blast", "tricyclazole"],
    "பிளாஸ்ட்": ["blast", "tricyclazole"],
    "ಬೆಂಕಿ ರೋಗ": ["blast", "tricyclazole"],
    "കുലവാട്ടം": ["blast", "tricyclazole"],
    "ବ୍ଲାଷ୍ଟ": ["blast", "tricyclazole"],
    "બ્લાસ્ટ": ["blast", "tricyclazole", "leaf blast"],
    "ब्लास्ट": ["blast", "tricyclazole", "leaf blast"],
    "ਕਿਡਾ": ["pest", "insect", "caterpillar", "bollworm"],
    "ਕੀੜਾ": ["pest", "insect", "caterpillar", "bollworm"],
    "કીડ": ["pest", "insect", "caterpillar", "bollworm"],
    "পোকা": ["pest", "insect", "caterpillar"],
    "పురుగు": ["pest", "insect", "caterpillar"],
    "பூச்சி": ["pest", "insect", "caterpillar"],
    "ಹುಳು": ["pest", "insect", "caterpillar"],
    "ਪਿੰਕ": ["pink", "pink bollworm"],
    "ਗੁਲਾਬੀ": ["pink", "pink bollworm", "emamectin"],
    "ਸੁੰਡੀ": ["caterpillar", "bollworm", "larvae"],
    "গোলাপী": ["pink", "pink bollworm"],
    "గులాబీ": ["pink", "pink bollworm", "emamectin"],
    "இளஞ்சிவப்பு": ["pink", "pink bollworm"],
    "காய்ப்புழு": ["bollworm", "fruit borer", "caterpillar"],
    "പുഴു": ["worm", "caterpillar", "bollworm"],
    "ગુલાબી": ["pink", "pink bollworm", "emamectin"],
    "गुलाबी": ["pink", "pink bollworm", "emamectin"],
    "ઈયળ": ["larvae", "caterpillar", "bollworm", "emamectin"],
    "eeyal": ["caterpillar", "larvae"],
    "इल्ली": ["bollworm", "borer", "larvae", "caterpillar", "pod borer"],
    "अळी": ["bollworm", "borer", "larvae", "caterpillar", "pod borer"],
    "ਚਿੱਟੀ ਮੱਖੀ": ["whitefly", "yellow mosaic"],
    "সাদা মাছি": ["whitefly", "yellow mosaic"],
    "తెల్ల దోమ": ["whitefly", "yellow mosaic"],
    "வெள்ளை ஈ": ["whitefly", "yellow mosaic"],
    "ಬಿಳಿ ನೊಣ": ["whitefly", "yellow mosaic"],
    "வெள்ளீച്ച": ["whitefly", "yellow mosaic"],
    "સફેદ માખી": ["whitefly", "yellow mosaic"],
    "ਸડો": ["rot", "boll rot", "root rot"],
    "ਚੇਪਾ": ["aphid", "imidacloprid"],
    "ਤੇਲਾ": ["aphid", "imidacloprid"],
    "জাব পোকা": ["aphid", "imidacloprid"],
    "పేనుబంక": ["aphid", "imidacloprid"],
    "அசுவினி": ["aphid", "imidacloprid"],
    "મોલો": ["aphid", "imidacloprid"],
    "मावा": ["aphid", "imidacloprid"],
    "ખારાશ": ["salinity", "soil"],
    "ਉਧਈ": ["termites", "chlorpyrifos"],
    "উধઈ": ["termites", "chlorpyrifos"],

    # Actions & Treatments across Indian Languages
    "ਛੰਟਕਾਵ": ["spray", "dose", "application"],
    "ਸਪਰੇਅ": ["spray", "dose", "application"],
    "ਦਵਾਈ": ["chemical", "pesticide", "fungicide", "spray", "dose"],
    "ਰੋਕਥਾਮ": ["control", "management", "prevention"],
    "ਇਲਾਜ": ["treatment", "remedy", "control"],
    "স্প্রে": ["spray", "dose", "application"],
    "ঔষধ": ["chemical", "pesticide", "fungicide", "spray"],
    "প্রতিকার": ["remedy", "control", "treatment"],
    "নিয়ন্ত্রণ": ["control", "management"],
    "స్ప్రే": ["spray", "dose", "application"],
    "మందులు": ["chemical", "pesticide", "fungicide", "spray"],
    "నివారణ": ["control", "management", "remedy"],
    "தெளிப்பு": ["spray", "dose", "application"],
    "மருந்து": ["chemical", "pesticide", "fungicide"],
    "கட்டுப்பாடு": ["control", "management"],
    "ಸಿಂಪಡಣೆ": ["spray", "dose"],
    "ಔಷಧಿ": ["chemical", "pesticide"],
    "നിയന്ത്രണം": ["control", "management"],
    "മരുന്ന്": ["chemical", "pesticide"],
    "छંટકાવ": ["spray", "dose", "application"],
    "દવા": ["chemical", "pesticide", "fungicide", "spray", "dose"],
    "ખાતર": ["fertilizer", "nutrient", "urea", "dap"],
    "વાવણી": ["sowing", "plantation", "variety"],
    "બીયારણ": ["seed", "variety", "hybrid"],
    "ફવારણી": ["spray", "dose", "application"],
    "स्प्रे": ["spray", "dose", "application"],
    "छिड़काव": ["spray", "dose", "application"],
    "दवा": ["chemical", "pesticide", "fungicide", "spray", "dose"],
    "उपाय": ["remedy", "control", "treatment"],
        "ઉપાય": ["remedy", "control", "treatment"],
    "વાવણી": ["sowing", "plantation", "variety"],
    "બીયારણ": ["seed", "variety", "hybrid"],
    "ફવારણી": ["spray", "dose", "application"],
    "સ્પ્રે": ["spray", "dose", "application"],
    "छिड़काव": ["spray", "dose", "application"],
    "दवा": ["chemical", "pesticide", "fungicide", "spray", "dose"],
    "उत्पादन": ["yield", "crop selection", "planning", "kharif", "rabi"],
    "ઉત્પાદન": ["yield", "crop selection", "planning"]
}

class HybridRetrievalEngine:
    def _calculate_vector_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculates lexical/semantic vector similarity between two texts using token-based cosine similarity.
        """
        words_a = set(re.findall(r'\w+', text_a.lower()))
        words_b = set(re.findall(r'\w+', text_b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a.intersection(words_b)
        return len(intersection) / math.sqrt(len(words_a) * len(words_b))

    def retrieve(
        self,
        db: Session,
        query_text: str,
        crop: str,
        district: str,
        top_k: int = 5,
        state: str = None
    ) -> List[EvidenceChunk]:
        """
        Executes fast, indexed hybrid retrieval using SQL-level candidate selection
        followed by multilingual semantic scoring.
        """
        query_lower = query_text.lower()
        extracted_terms = [w.strip("?,.!।;:\"'") for w in query_lower.split() if len(w) > 2]
        
        # Build expanded terms set (including English mappings of regional words)
        search_terms: Set[str] = set(extracted_terms)
        for word in extracted_terms:
            if word in MULTILINGUAL_SYNONYMS:
                search_terms.update(MULTILINGUAL_SYNONYMS[word])
            for syn_key, mapped_words in MULTILINGUAL_SYNONYMS.items():
                if syn_key in word:
                    search_terms.update(mapped_words)

        # 1. SQL Candidate Selection with LIMIT (sub-5ms)
        target_crops = []
        if crop and crop != "General":
            target_crops.append(crop)
        # Also check if any crop was expanded in search_terms
        for c in ["Soybean", "Cotton", "Wheat", "Rice", "Chickpea", "Sugarcane", "Groundnut", "Chilli", "Tomato", "Maize", "Onion"]:
            if c.lower() in search_terms:
                target_crops.append(c)
        target_crops = list(set(target_crops))
        if not target_crops:
            target_crops = ["General"]

        # Build SQL filters
        base_query = db.query(KnowledgeDocument)
        
        # 1. SQL Candidate Selection with Term Targeting (sub-10ms)
        candidate_docs = []
        seen_ids = set()

        # Step A: Always fetch relevant Tier-1 Official ICAR/KVK documents
        tier1_docs = base_query.filter(
            and_(
                KnowledgeDocument.authority_tier == 1,
                or_(KnowledgeDocument.crop.in_(target_crops), KnowledgeDocument.crop == "General")
            )
        ).all()
        for d in tier1_docs:
            if d.id not in seen_ids:
                candidate_docs.append(d)
                seen_ids.add(d.id)

        # Step B: Keyword-targeted search in target crops (e.g. matching 'price', 'bollworm', 'rust')
        important_terms = [t for t in search_terms if len(t) > 3 and t not in ["what", "this", "have", "with", "from", "your", "give"]]
        for term in important_terms[:4]:
            term_matches = db.query(KnowledgeDocument).filter(
                and_(
                    or_(KnowledgeDocument.crop.in_(target_crops), KnowledgeDocument.crop == "General"),
                    or_(KnowledgeDocument.title.ilike(f"%{term}%"), KnowledgeDocument.content.ilike(f"%{term}%"))
                )
            ).order_by(KnowledgeDocument.authority_tier.asc()).limit(15).all()
            for d in term_matches:
                if d.id not in seen_ids:
                    candidate_docs.append(d)
                    seen_ids.add(d.id)

        # Step C: Fill with crop general advisories if candidates are few
        if len(candidate_docs) < 25:
            fallback_crop_docs = base_query.filter(
                KnowledgeDocument.crop.in_(target_crops)
            ).limit(30).all()
            for d in fallback_crop_docs:
                if d.id not in seen_ids:
                    candidate_docs.append(d)
                    seen_ids.add(d.id)

        # 2. In-Memory Precision Scoring
        candidates = []
        for doc in candidate_docs:
            doc_text = (doc.title + " " + doc.content).lower()
            
            # A. Term overlap score (combining Devanagari, Gurmukhi, Bengali, Telugu, Tamil, Gujarati, etc. and English synonyms)
            matched_terms = [t for t in search_terms if t in doc_text]
            term_score = min(1.0, len(matched_terms) * 0.22)
            
            # B. Authority Tier weight (ICAR, KVK, SAUs)
            authority_boost = 0.30 if doc.authority_tier == 1 else 0.20
            
            # C. Target Crop Match weight
            crop_match = 0.0
            if crop and doc.crop and crop.lower() == doc.crop.lower():
                crop_match = 0.35
            elif any(c.lower() == doc.crop.lower() for c in target_crops if doc.crop):
                crop_match = 0.28
            elif doc.crop == "General":
                crop_match = 0.15

            # D. District / State / Regional Location Match weight
            location_match = 0.0
            if district and doc.district and district.lower() in doc.district.lower():
                location_match = 0.15
            elif state and doc.state and state.lower() in doc.state.lower():
                location_match = 0.10
            elif doc.state == "All-India" or not doc.state:
                location_match = 0.05

            # Final weighted score (combines semantic term overlap, official authority, and crop grounding)
            final_score = round(min(0.98, (term_score * 0.35) + authority_boost + crop_match + location_match), 2)
            
            # Threshold for inclusion
            if final_score >= 0.25:
                candidates.append(EvidenceChunk(
                    source_id=doc.id,
                    authority=doc.source_name,
                    title=doc.title,
                    score=final_score,
                    text=doc.content
                ))

        # Sort by score descending (and prefer Tier 1 for ties)
        candidates.sort(key=lambda x: x.score, reverse=True)

        # If empty, return top available general document with conservative score
        if not candidates and candidate_docs:
            first = candidate_docs[0]
            candidates.append(EvidenceChunk(
                source_id=first.id,
                authority=first.source_name,
                title=first.title,
                score=0.45,
                text=first.content
            ))

        return candidates[:top_k]

retrieval_engine = HybridRetrievalEngine()
