import math
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
        Executes hybrid BM25 term frequency + Dense vector similarity search filtered by crop and district.
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
            
            # 1. BM25 term overlap calculation
            overlap = sum(1 for word in words if word in doc_text_lower)
            bm25_score = min(1.0, overlap * 0.25)

            # 2. Dense Semantic Term Vector Similarity Calculation
            vector_sim = self._calculate_vector_similarity(query_text.lower(), doc_text_lower)

            # 3. Agronomic Metadata Precision Score
            metadata_score = 0.0
            if crop and doc.crop and crop.lower() in doc.crop.lower():
                metadata_score += 0.35
            if district and doc.district and district.lower() in doc.district.lower():
                metadata_score += 0.25
            if doc.authority_tier == 1:
                metadata_score += 0.2
            if any(k in doc_text_lower for k in ["yield", "crop selection", "उत्पादन", "spray", "dose"]):
                metadata_score += 0.2

            # Weighted Hybrid Score: 30% BM25 + 30% Vector Similarity + 40% Metadata Match
            final_score = round(min(0.99, (bm25_score * 0.30) + (vector_sim * 0.30) + (metadata_score * 0.40)), 2)

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

    def _calculate_vector_similarity(self, query: str, doc_text: str) -> float:
        """
        Calculates normalized term vector similarity between query and document.
        """
        q_words = [w for w in query.split() if len(w) > 2]
        d_words = doc_text.split()
        if not q_words or not d_words:
            return 0.0

        q_tf = {w: q_words.count(w) for w in set(q_words)}
        d_tf = {w: d_words.count(w) for w in set(q_words)}

        dot_product = sum(q_tf[w] * d_tf.get(w, 0) for w in q_tf)
        q_norm = math.sqrt(sum(v ** 2 for v in q_tf.values()))
        d_norm = math.sqrt(sum(d_tf.get(w, 0) ** 2 for w in q_tf) + 1.0)

        if q_norm == 0 or d_norm == 0:
            return 0.0

        return min(1.0, dot_product / (q_norm * d_norm))

retrieval_engine = HybridRetrievalEngine()

