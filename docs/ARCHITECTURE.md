# FasalMitra — Architecture & Integration Specification

## 1. System Overview & Core Philosophy

FasalMitra is built on a **Retrieval-First, Grounding-First, Safety-First** paradigm. Rather than directly feeding farmer voice inputs into a generative LLM, the system processes every request through a 14-stage modular pipeline:

```text
[ Farmer Speech / Text ]
         │
         ▼
[ 1. ASR & Transcript Normalization ]
         │
         ▼
[ 2. Language Detection ]
         │
         ▼
[ 3. Query Understanding & Entity Extraction ]
         │
         ▼
[ 4. Farmer, Crop Passport & Weather Context Engine ]
         │
         ▼
[ 5. Pre-LLM Safety Gate ]  ── (Failed) ──► [ Clarification / Escalation ]
         │ (Passed)
         ▼
[ 6. Hybrid Retriever (BM25 + Vector Search) ]
         │
         ▼
[ 7. Cross-Encoder & Metadata Reranker ]
         │
         ▼
[ 8. Grounding Gate (Evidence Sufficiency Check) ] ── (Insufficient) ──► [ Escalation Engine ]
         │ (Sufficient)
         ▼
[ 9. LLM Grounded Prompt Generator ]
         │
         ▼
[ 10. Claim Extractor & Verification Engine ] ── (Unsupported) ──► [ Reject & Regenerate / Escalate ]
         │ (Verified)
         ▼
[ 11. Multi-factor Confidence Engine ] ── (Low Score) ──► [ Expert Dashboard Queue ]
         │ (High/Medium Score)
         ▼
[ 12. Multilingual Translation Layer ]
         │
         ▼
[ 13. TTS Audio Synthesizer ]
         │
         ▼
[ 14. Immutable Audit Logger ]
```

---

## 2. Key Component Responsibilities & Integrations

### 2.1 Interaction Layer (`backend/app/core/asr_engine.py` & `tts_engine.py`)
- **ASR Engine:** Receives raw audio streams (WAV, MP3, OGG from Phone calls or WhatsApp voice notes), detects spoken language (Hindi, Marathi, Gujarati, English), normalizes speech artifacts, and produces structured transcripts. Supports live APIs (Whisper/IndicASR) and offline fallback handlers.
- **TTS Engine:** Takes final verified, grounded advisory text in the target language and generates voice responses formatted for phone playback or WhatsApp voice note delivery.

### 2.2 Agricultural Intelligence & Context Layer (`backend/app/core/context_engine.py` & `query_understanding.py`)
- **Query NLP:** Parses raw transcripts into canonical intents (`PEST`, `DISEASE`, `FERTILIZER`, `IRRIGATION`, `SOWING`, `WEATHER`) and extracts structured agronomic entities (Crop name, variety, symptoms, chemicals, crop stage in days/weeks, location).
- **Context Engine:** Combines farmer preferences, crop passports, multi-turn session dialogue history (`messages` table), and live IMD agromet weather snapshots to enrich the query payload and handle natural follow-up questions.

### 2.3 Knowledge & Grounding Layer (`backend/app/core/retrieval_engine.py`, `reranker.py`, `grounding_gate.py`)
- **Hybrid Retrieval:** Combines BM25 term frequency matching with dense semantic term vector similarity scoring over ingested ICAR/KVK/KCC authoritative documents filtered by location, crop, and crop stage.
- **Reranker:** Evaluates retrieved candidates based on agronomic relevance, district match, publication freshness, and source authority.
- **Grounding Gate:** Evaluates whether retrieved evidence provides 100% sufficient basis to answer the question without hallucination.


### 2.4 Safety & Generation Layer (`backend/app/core/safety_gate.py`, `llm_generator.py`, `claim_verifier.py`)
- **Pre-Safety Gate:** Blocks out-of-domain requests, unsafe chemical combinations, or high-risk requests missing critical stage/dosage details.
- **Grounded LLM Generator:** Prompts the LLM with strict instructions to restrict statements ONLY to supplied retrieved evidence chunks.
- **Claim Verifier:** Extracts quantitative claims (e.g., "Spray 2ml/L of Chlorpyrifos") and verifies each claim against original retrieved document text.

### 2.5 Expert Escalation & Audit Layer (`backend/app/core/escalation_engine.py` & `audit_logger.py`)
- **Escalation Engine:** Automatically packages low-confidence or high-risk cases into structured payloads and pushes them to the human Expert Dashboard.
- **Audit Logger:** Writes immutable event records for every stage (`QUERY_RECEIVED`, `ASR_COMPLETED`, `RETRIEVAL_COMPLETED`, `GROUNDING_PASSED`, `CLAIM_VERIFIED`, `EXPERT_ESCALATED`) for auditability.
