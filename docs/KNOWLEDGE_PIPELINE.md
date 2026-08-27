# FasalMitra — Knowledge Pipeline & Ingestion Architecture

## 1. Knowledge Ingestion Pipeline Architecture

```text
[ Authoritative Sources: ICAR / KVK / KCC / IMD ]
                       │
                       ▼
            [ Document Collector ]
                       │
                       ▼
          [ Normalizer & Cleaner ]
                       │
                       ▼
     [ Metadata Enrichment Engine ]
     (Crop, Stage, District, Season, Expiry)
                       │
                       ▼
           [ Agronomic Chunker ]
     (Preserves recommendations intact)
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
 [ BM25 Inverted Index ]   [ Vector Embedding Engine ]
 (Exact Agronomic Terms)   (Dense Semantic Index)
          │                         │
          └────────────┬────────────┘
                       ▼
            [ Hybrid Knowledge Store ]
```

---

## 2. Ingestion Rules & Metadata Extraction

Every chunk ingested into FasalMitra must contain rich metadata:

```json
{
  "chunk_id": "KVK-LAT-2025-SOY-001",
  "document_id": "DOC-KVK-2025-88",
  "source_name": "KVK Latur Advisory Bulletin",
  "authority_tier": 1, // 1: KVK/ICAR Official, 2: IMD, 3: KCC Historical
  "crop": "Soybean",
  "variety": "JS 335",
  "crop_stage_min_days": 20,
  "crop_stage_max_days": 45,
  "district": "Latur",
  "state": "Maharashtra",
  "season": "Kharif",
  "valid_from": "2025-06-01",
  "valid_until": "2026-10-31",
  "text": "For controlling Yellow Mosaic Virus in soybean caused by whitefly vector, spray Thiamethoxam 25% WG at 100g/ha in 500L water when whitefly population exceeds 5 per plant."
}
```

---

## 3. Freshness & Conflict Resolution

- **Freshness Rule:** Documents past their `valid_until` date are flagged as `STALE` and deprioritized during reranking.
- **Conflict Engine:** If two documents give contradictory dosage or chemical guidance for the same crop/district:
  1. Compares `authority_tier` (KVK Official > Historical Q&A).
  2. Compares `publication_date` (Newer bulletin overrides older).
  3. If unresolved, marks status as `CONFLICTING` and escalates to Expert Dashboard.
