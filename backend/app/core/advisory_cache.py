import time
import hashlib
from typing import Optional, Dict, Any

class AdvisoryCache:
    """
    High-Performance In-Memory Semantic Advisory Cache with Time-To-Live (TTL).
    Caches verified, safety-approved ICAR agricultural advisories to deliver
    sub-50ms responses for recurring seasonal inquiries and protect against LLM API rate limits.
    """
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, crop: str, target_or_intent: str, lang: str, district: str, state: str) -> str:
        raw = f"{crop or ''}:{target_or_intent or ''}:{lang or ''}:{district or ''}:{state or ''}".lower()
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def get(self, crop: str, target_or_intent: str, lang: str, district: str = "", state: str = "") -> Optional[Dict[str, Any]]:
        if not crop or not target_or_intent:
            return None
        key = self._make_key(crop, target_or_intent, lang, district, state)
        item = self._cache.get(key)
        if not item:
            return None
        # Check TTL expiry
        if time.time() - item["timestamp"] > self.ttl:
            del self._cache[key]
            return None
        return item["data"]

    def set(self, crop: str, target_or_intent: str, lang: str, data: Dict[str, Any], district: str = "", state: str = ""):
        if not crop or not target_or_intent:
            return
        key = self._make_key(crop, target_or_intent, lang, district, state)
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data
        }

    def clear(self):
        self._cache.clear()

advisory_cache = AdvisoryCache(ttl_seconds=3600)
