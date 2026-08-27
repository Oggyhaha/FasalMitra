from typing import List
from backend.app.schemas.schemas import EvidenceChunk

class AgronomicReranker:
    def rerank(self, candidates: List[EvidenceChunk], crop: str, stage_days: int, district: str) -> List[EvidenceChunk]:
        """
        Reranks evidence chunks using cross-encoder relevance heuristics.
        """
        reranked = []
        for chunk in candidates:
            score = chunk.score
            # Boost official KVK/ICAR bulletins
            if "KVK" in chunk.authority or "ICAR" in chunk.authority:
                score += 0.05
            
            # Boost if district matches in title or text
            if district.lower() in chunk.text.lower():
                score += 0.05

            chunk.score = min(0.99, round(score, 2))
            reranked.append(chunk)

        reranked.sort(key=lambda x: x.score, reverse=True)
        return reranked

reranker = AgronomicReranker()
