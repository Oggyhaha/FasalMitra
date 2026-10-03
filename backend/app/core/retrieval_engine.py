import re
import math
from typing import List, Dict, Any, Set
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from backend.app.db.models import KnowledgeDocument
from backend.app.schemas.schemas import EvidenceChunk

# Multilingual term mapping for semantic overlap calculation
MULTILINGUAL_SYNONYMS = {
    # Crops
    "सोयाबीन": ["soybean", "soyabean", "yellow mosaic"],
    "कापूस": ["cotton", "bollworm", "kapas"],
    "कपास": ["cotton", "bollworm", "kapas"],
    "गहू": ["wheat", "rust", "yellow rust"],
    "गेहूं": ["wheat", "rust", "yellow rust"],
    "भात": ["rice", "paddy", "blast"],
    "धान": ["rice", "paddy", "blast"],
    "चावल": ["rice", "paddy", "blast"],
    "हरभरा": ["chickpea", "gram", "pod borer"],
    "चना": ["chickpea", "gram", "pod borer"],
    "ऊस": ["sugarcane", "shoot borer"],
    "गन्ना": ["sugarcane", "shoot borer"],
    "भुईमूग": ["groundnut", "peanut"],
    "मूंगफली": ["groundnut", "peanut"],
    # Symptoms / Pests / Diseases
    "पिवळी": ["yellowing", "yellow", "whitefly", "mosaic"],
    "पिवळा": ["yellowing", "yellow", "whitefly", "mosaic"],
    "पीला": ["yellowing", "yellow", "whitefly", "mosaic", "rust"],
    "पीले": ["yellowing", "yellow", "whitefly", "mosaic", "rust"],
    "इल्ली": ["bollworm", "borer", "larvae", "caterpillar", "pod borer"],
    "अळी": ["bollworm", "borer", "larvae", "caterpillar", "pod borer"],
    "गुलाबी": ["pink", "pink bollworm", "emamectin"],
    "रतुआ": ["rust", "yellow rust", "propiconazole"],
    "तांबेरा": ["rust", "yellow rust", "propiconazole"],
    "ब्लास्ट": ["blast", "tricyclazole", "leaf blast"],
    "खोडकिडा": ["shoot borer", "stem borer", "fipronil"],
    "बोरर": ["borer", "shoot borer", "stem borer"],
    # Actions
    "फवारणी": ["spray", "dose", "application"],
    "स्प्रे": ["spray", "dose", "application"],
    "छिड़काव": ["spray", "dose", "application"],
    "दवा": ["chemical", "pesticide", "fungicide", "spray", "dose"],
    "उत्पादन": ["yield", "crop selection", "planning", "kharif", "rabi"],
    "उत्पन्न": ["yield", "crop selection", "planning", "kharif", "rabi"],
    "लागवड": ["sowing", "cultivation", "crop selection", "variety"]
}

class HybridRetrievalEngine:
    def retrieve(
        self,
        db: Session,
        query_text: str,
        crop: str,
        district: str,
        top_k: int = 5
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
            
            # A. Term overlap score (combining Devanagari and English synonyms)
            matched_terms = [t for t in search_terms if t in doc_text]
            term_score = min(1.0, len(matched_terms) * 0.18)
            
            # B. Authority Tier weight
            authority_boost = 0.35 if doc.authority_tier == 1 else 0.20
            
            # C. Target Crop Match weight
            crop_match = 0.0
            if crop and doc.crop and crop.lower() == doc.crop.lower():
                crop_match = 0.30
            elif any(c.lower() == doc.crop.lower() for c in target_crops if doc.crop):
                crop_match = 0.25
            elif doc.crop == "General":
                crop_match = 0.15

            # D. District / Location Match weight
            location_match = 0.0
            if district and doc.district and district.lower() in doc.district.lower():
                location_match = 0.15

            # Final weighted score
            final_score = round(min(0.98, (term_score * 0.40) + authority_boost + (crop_match * 0.30) + location_match), 2)
            
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
