# FasalMitra — Data Model & Schema Specification

## 1. Entity-Relationship Overview

```text
  ┌───────────────┐           ┌───────────────┐
  │    Farmer     │1       *  │     Farm      │
  │───────────────│───────────│───────────────│
  │ id            │           │ id            │
  │ phone_number  │           │ farmer_id     │
  │ language      │           │ location      │
  │ district      │           │ district      │
  └───────┬───────┘           └───────┬───────┘
          │ 1                         │ 1
          │                           │
          │ *                         │ *
  ┌───────┴───────┐           ┌───────┴───────┐
  │ Conversation  │           │ Crop Passport │
  │───────────────│           │───────────────│
  │ id            │           │ id            │
  │ farmer_id     │           │ farm_id       │
  │ channel       │           │ crop_name     │
  └───────┬───────┘           │ sowing_date   │
          │ 1                 │ stage_days    │
          │                   └───────────────┘
          │ *
  ┌───────┴───────┐           ┌───────────────┐
  │    Message    │1       1  │ QueryContext  │
  │───────────────│───────────│───────────────│
  │ id            │           │ id            │
  │ conversation  │           │ message_id    │
  │ text / audio  │           │ intent        │
  └───────┬───────┘           │ weather_snap  │
          │ 1                 └───────────────┘
          │
          ├───────────────────┬───────────────────┐
          │ 1                 │ 1                 │ 1
          ▼                   ▼                   ▼
  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
  │   Retrieval   │   │  SafetyCheck  │   │  Escalation   │
  │───────────────│   │───────────────│   │───────────────│
  │ id            │   │ id            │   │ id            │
  │ documents     │   │ pre_status    │   │ reason        │
  │ grounding     │   │ claims_check  │   │ expert_id     │
  └───────────────┘   └───────────────┘   └───────────────┘
```

---

## 2. Core Schemas

### 2.1 Farmer & Farm Schemas
- `farmers`: `id`, `name`, `phone_number`, `preferred_language`, `state`, `district`, `created_at`
- `farms`: `id`, `farmer_id`, `farm_name`, `area_acres`, `soil_type`, `district`, `state`
- `crop_passports`: `id`, `farm_id`, `crop_name`, `variety`, `sowing_date`, `stage_days`, `season`

### 2.2 Knowledge & Index Schemas
- `knowledge_documents`: `id`, `source_type` (ICAR, KVK, KCC, IMD), `authority_tier` (1 to 5), `title`, `district`, `state`, `crop`, `publication_date`, `valid_until`, `content`
- `knowledge_chunks`: `id`, `document_id`, `chunk_index`, `text`, `embedding_json`, `metadata_json`

### 2.3 Execution & Audit Schemas
- `conversations`: `id`, `farmer_id`, `channel`, `status`, `started_at`
- `messages`: `id`, `conversation_id`, `sender` (FARMER / SYSTEM / EXPERT), `raw_text`, `audio_url`, `language`
- `query_contexts`: `id`, `message_id`, `intent`, `crop`, `symptoms`, `stage`, `district`, `weather_summary`
- `retrievals`: `id`, `query_context_id`, `retrieved_chunks_json`, `rerank_scores_json`, `grounding_status`
- `safety_checks`: `id`, `query_context_id`, `pre_safety_passed`, `claims_json`, `post_safety_passed`, `confidence_score`
- `escalations`: `id`, `message_id`, `farmer_id`, `question`, `risk_level`, `reason`, `status`, `expert_answer`
- `audit_events`: `id`, `query_id`, `event_type`, `payload_json`, `timestamp`
