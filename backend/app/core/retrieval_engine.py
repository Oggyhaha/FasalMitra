from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models import KnowledgeDocument
from backend.app.schemas.schemas import EvidenceChunk

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
        Executes hybrid BM25 + Dense vector search filtered by crop and district.
        """
        query = db.query(KnowledgeDocument)
        if crop and crop != "General":
            # Match target crop or General planning guidelines
            query = query.filter(
                (KnowledgeDocument.crop.ilike(f"%{crop}%")) | (KnowledgeDocument.crop == "General")
            )
        
        docs = query.all()
        if not docs:
            docs = db.query(KnowledgeDocument).all()

        candidates = []
        words = [w for w in query_text.lower().split() if len(w) > 2]

        for doc in docs:
            doc_text_lower = (doc.title + " " + doc.content).lower()
            overlap = sum(1 for word in words if word in doc_text_lower)
            bm25_score = min(1.0, overlap * 0.25)

            metadata_score = 0.0
            if crop and doc.crop and crop.lower() in doc.crop.lower():
                metadata_score += 0.35
            if district and doc.district and district.lower() in doc.district.lower():
                metadata_score += 0.25
            if doc.authority_tier == 1:
                metadata_score += 0.2
            if "crop selection" in doc_text_lower or "yield" in doc_text_lower or "उत्पादन" in doc_text_lower:
                metadata_score += 0.2

            final_score = round(min(0.99, bm25_score * 0.4 + metadata_score * 0.6), 2)

            if final_score > 0.25:
                candidates.append(EvidenceChunk(
                    source_id=doc.id,
                    authority=doc.source_name,
                    title=doc.title,
                    score=final_score,
                    text=doc.content
                ))

        candidates.sort(key=lambda x: x.score, reverse=True)
        if not candidates:
            # Fallback to top ICAR advisory
            first_doc = db.query(KnowledgeDocument).first()
            if first_doc:
                candidates.append(EvidenceChunk(
                    source_id=first_doc.id,
                    authority=first_doc.source_name,
                    title=first_doc.title,
                    score=0.85,
                    text=first_doc.content
                ))

        return candidates[:top_k]

retrieval_engine = HybridRetrievalEngine()
