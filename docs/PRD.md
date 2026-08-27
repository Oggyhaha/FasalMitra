# FasalMitra — Complete Functional PRD

**Product Name:** FasalMitra  
**Product Type:** Voice-first multilingual agricultural advisory platform  
**Track:** Engineering  
**Domain:** Agriculture  
**PRD Version:** 1.0  
**Status:** Development Baseline  
**Primary Channels:** Phone + WhatsApp  
**Primary Users:** Farmers  
**Secondary Users:** Agricultural Experts, Administrators  
**Architecture Principle:** Retrieval-first, grounding-first, safety-first  

---

## 1. Product Definition

### 1.1 What is FasalMitra?
FasalMitra allows farmers to ask agricultural questions naturally using voice or text in their regional language.

The system understands the question, determines the relevant agricultural context, retrieves trusted agricultural evidence, validates whether that evidence is sufficient, generates an answer only when justified, validates the generated answer, and either:
1. Answers the farmer;
2. Asks for missing information; or
3. Escalates the case to an agricultural expert.

```text
                    FASALMITRA PIPELINE
                        │
          ┌─────────────┴─────────────┐
          │                           │
       Phone                      WhatsApp
          │                           │
         ASR                    Text / Audio
          │                           │
          └─────────────┬─────────────┘
                        ↓
                Language Detection
                        ↓
                Query Understanding
                        ↓
             Farmer / Crop Context
                        ↓
                 Weather Context
                        ↓
                 PRE-SAFETY GATE
                        ↓
                 Hybrid Retrieval
                        ↓
                    Reranking
                        ↓
                Grounding Check
                        ↓
              ┌─────────┴─────────┐
              │                   │
          Insufficient          Sufficient
              │                   │
       Clarify / Escalate        LLM
                                  ↓
                         POST-SAFETY VALIDATION
                                  ↓
                            Confidence Check
                                  ↓
                         ┌────────┴────────┐
                         │                 │
                     Answer            Escalate
                         │
                     Translation
                         ↓
                        TTS
                         ↓
                       Farmer
```

---

## 2. Product Philosophy

FasalMitra follows six core principles:

- **P1 — Evidence before generation:** The LLM never becomes the primary source of agricultural truth.
- **P2 — Safety before convenience:** If the system cannot safely answer, it must not guess.
- **P3 — Context matters:** Agricultural recommendations depend on crop, variety, stage, location, season, weather, problem, and timing.
- **P4 — Voice is an interface:** ASR and TTS belong to the interaction layer. The agricultural intelligence remains channel-independent.
- **P5 — Human experts remain part of the system:** FasalMitra augments experts; it does not claim to replace them.
- **P6 — Every actionable answer must be auditable:** The system must explain internally why an answer was given.

---

## 3. Product Scope & Functional Requirements

- **FR-001 — Channel Entry:** Accept Phone calls, WhatsApp text, and WhatsApp voice messages.
- **FR-002 — Language Selection:** Automatic language detection with manual fallback.
- **FR-003 — ASR & Transcript Normalization:** Clean speech audio into structured text while retaining original transcript.
- **FR-004 — Query Understanding:** Extract intent, crop, variety, symptoms, chemicals, irrigation, sowing, harvest, location, and urgency.
- **FR-005 — Context Resolution:** Combine farmer profile, crop passport, crop stage, and live IMD agromet weather context.
- **FR-006 — Hybrid Retrieval & Reranking:** Combine BM25 keyword matching, vector dense retrieval, and cross-encoder reranking over KCC, ICAR, and KVK data.
- **FR-007 — Grounding Gate:** Validate evidence sufficiency before LLM generation (SUPPORTED / INSUFFICIENT / CONFLICTING / STALE).
- **FR-008 — Safety Gates:** Pre-LLM refusal for unsafe chemical combinations or missing context; Post-LLM claim extraction and verification.
- **FR-009 — Confidence & Escalation Engine:** Compute overall confidence score (High/Medium/Low) and queue low-confidence/high-risk queries for human expert review.
- **FR-010 — Multilingual Translation & TTS:** Convert validated answers into target regional languages and synthesize natural audio responses.
