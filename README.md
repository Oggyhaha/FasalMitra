# FasalMitra 🌾

### Voice-First Multilingual Agri-Advisory

FasalMitra is a production-oriented, safety-first agricultural advisory system designed for farmers who may not be literate, may not own a smartphone, or may not be comfortable using Hindi/English.

A farmer can interact through an **ordinary phone call or WhatsApp**, speak in a regional Indian language, and receive an answer in the same language.

The core design principle is:

> **FasalMitra does not treat the LLM as the source of agricultural truth. It retrieves evidence from trusted agricultural sources, validates that evidence, generates a grounded answer, and checks the answer again before speaking it to the farmer.**

---

## 1. Problem We Solve

Most agricultural advisory applications assume that farmers:

- can read and type;
- use a smartphone;
- understand Hindi or English;
- can navigate complex applications.

FasalMitra instead provides a **voice-first, multilingual, evidence-grounded** interface.

The target advisory scope includes:

- crop questions;
- sowing windows;
- irrigation;
- crop-stage guidance;
- crop symptoms;
- input-use questions;
- weather-aware agricultural decisions;
- localized advisories.

High-risk or poorly grounded cases are **not guessed**. They are routed to an expert or handled through a clarification flow.

---

## 2. Core Principles

### 2.1 Evidence over hallucination

The LLM must not independently invent agronomic recommendations.

### 2.2 Retrieval before generation

Relevant ICAR/KVK/IMD/KCC evidence is retrieved before the LLM generates an answer.

### 2.3 Safety before and after the LLM

- **Pre-LLM safety:** reject out-of-scope, unsafe, or insufficiently specified requests.
- **Post-LLM safety:** verify that generated claims are supported by retrieved evidence.

### 2.4 Confidence-aware answering

If evidence is weak, conflicting, stale, or irrelevant, FasalMitra should abstain, ask for clarification, or escalate to an expert.

### 2.5 Local context matters

Agricultural advice should consider:

- location;
- crop;
- crop stage;
- sowing date;
- season;
- weather;
- farmer context.

### 2.6 Voice is an interaction layer

ASR and TTS are not the agricultural reasoning engine.

```text
ASR = speech → text
TTS = validated text → speech
```

---

# 3. High-Level Architecture

```text
                              ┌──────────────────┐
                              │      FARMER      │
                              └────────┬─────────┘
                                       │
                           ┌───────────┴───────────┐
                           │                       │
                      Phone Call               WhatsApp
                           │                       │
                           └───────────┬───────────┘
                                       │
                              VOICE / INTERACTION
                                       │
                                      ASR
                                       │
                                       ▼
                           ┌──────────────────────┐
                           │ Query Understanding  │
                           │ Intent / Entities    │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ Context Engine       │
                           │ Crop / Location      │
                           │ Stage / Weather      │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ PRE-LLM SAFETY       │
                           └──────────┬───────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────┐
                    │      HYBRID RETRIEVAL           │
                    │ Vector + Keyword + Metadata     │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  RERANKER   │
                              └──────┬──────┘
                                     │
                                     ▼
                           ┌──────────────────────┐
                           │ Grounding Check      │
                           └──────────┬───────────┘
                                      │
                              ┌───────┴────────┐
                              │                │
                         insufficient       sufficient
                              │                │
                              ▼                ▼
                         EXPERT /         LLM GENERATION
                         CLARIFY               │
                                               ▼
                                    ┌──────────────────────┐
                                    │ POST-LLM SAFETY      │
                                    │ Claim Verification   │
                                    └──────────┬───────────┘
                                               │
                                               ▼
                                      CONFIDENCE CHECK
                                               │
                                    ┌──────────┴─────────┐
                                    │                    │
                                  LOW                  HIGH
                                    │                    │
                                    ▼                    ▼
                                  EXPERT              Translation
                                                       │
                                                       ▼
                                                       TTS
                                                       │
                                                       ▼
                                                  Farmer
```

---

# 4. Knowledge Architecture

Agricultural sources are not connected directly to Query Understanding.

They first enter a **knowledge ingestion pipeline**.

```text
ICAR ─────┐
KVK ──────┤
KCC ──────┤
IMD ──────┘
           │
           ▼
   Document/Data Ingestion
           │
           ▼
   Parsing + OCR if needed
           │
           ▼
      Cleaning
           │
           ▼
    Metadata Extraction
           │
           ▼
        Chunking
           │
           ▼
       Embeddings
           │
           ▼
 PostgreSQL + pgvector
 + keyword/full-text index
```

## Source roles

| Source | Role in FasalMitra |
|---|---|
| **ICAR** | Authoritative agricultural research and extension knowledge |
| **KVK** | Localized agricultural advisories and extension knowledge |
| **KCC** | Real farmer questions, language patterns, FAQ-style examples and evaluation data |
| **IMD** | Weather and agrometeorological context/advisories |
| **AI4Bharat IndicTrans2** | Indian-language translation technology |

KCC should not automatically be treated as equivalent to a current authoritative recommendation. Source authority, freshness, and relevance are tracked as metadata.

---

# 5. Technology Stack

## Frontend

- Next.js
- React
- Tailwind CSS

### Why?

The project needs:

- farmer/profile views;
- expert dashboard;
- evidence/source display;
- escalation management;
- analytics;
- testing interfaces.

Next.js gives a strong production web foundation while React/Tailwind enable rapid UI development.

---

## Backend

- Python
- FastAPI

### Why?

Python has the strongest ecosystem for:

- NLP;
- speech models;
- embeddings;
- transformers;
- document processing;
- RAG;
- evaluation.

FastAPI provides typed, high-performance HTTP APIs and works naturally with Python AI services.

---

## Database

### PostgreSQL

Used for durable application data:

- users/farmers;
- farms;
- crops;
- crop cycles;
- conversations;
- messages;
- advisories;
- sources;
- experts;
- escalations;
- feedback;
- audit records.

### pgvector

Used for vector embeddings and semantic retrieval inside PostgreSQL.

This keeps the first production architecture simpler than immediately introducing a separate vector database.

---

## Redis

Used for:

- session state;
- short-lived conversation state;
- caching;
- rate limiting;
- queues/background jobs where appropriate.

Think:

```text
PostgreSQL = durable memory
Redis      = fast temporary state
```

---

## ASR

Use an **Indic-capable ASR model**, benchmarked on actual farmer/telephone/WhatsApp audio.

Candidate families include:

- IndicWhisper / Whisper-family models;
- IndicConformer or other Indic ASR systems;
- managed speech APIs if they outperform self-hosted models for the target languages.

### Selection principle

Do not select ASR only by popularity.

Benchmark:

- Word Error Rate (WER);
- language accuracy;
- agricultural terminology accuracy;
- noisy audio performance;
- phone-call performance;
- code-switching performance;
- latency.

---

## Translation

### AI4Bharat IndicTrans2

Used where cross-language translation is needed.

Example:

```text
Marathi farmer speech
        ↓
ASR
        ↓
Normalized/internal representation
        ↓
Knowledge retrieval + reasoning
        ↓
Validated answer
        ↓
IndicTrans2
        ↓
Marathi answer
```

Translation should not be allowed to introduce unsupported agronomic claims. The authoritative content is validated before final speech output.

---

## Embeddings

Use a strong multilingual embedding model suitable for Indian languages.

Purpose:

```text
document → vector
question → vector
```

Similar meanings become searchable even when wording differs.

Example:

```text
"सोयाबीनची पाने पिवळी पडली"
```

can retrieve English/Hindi/Marathi material discussing soybean yellowing.

---

## Hybrid Retrieval

FasalMitra should combine:

1. **Vector/semantic search**
2. **Keyword/full-text search**
3. **Metadata filtering**

### Why?

| Method | Strength |
|---|---|
| Vector search | semantic meaning |
| Keyword search | exact agricultural terms, chemicals, numbers, varieties |
| Metadata filtering | crop/location/stage/season/source constraints |

---

## Reranking

Hybrid retrieval may return many candidates.

A reranker selects the most relevant evidence.

Ranking signals should include:

- semantic relevance;
- source authority;
- crop match;
- location match;
- crop-stage match;
- freshness;
- advisory validity;
- weather relevance;
- source agreement.

---

# 6. Query Understanding

Example farmer question:

> "माझ्या सोयाबीनला पानं पिवळी पडली आहेत, काय करू?"

The system converts it into structured information:

```json
{
  "language": "mr",
  "intent": "crop_symptom",
  "crop": "soybean",
  "symptom": "yellowing"
}
```

Context can add:

```json
{
  "location": "Pune, Maharashtra",
  "crop_stage": "vegetative",
  "season": "Kharif",
  "sowing_date": "..."
}
```

Important entities include:

- crop;
- variety;
- symptom;
- pest/disease;
- input;
- fertilizer;
- chemical;
- location;
- date;
- crop stage;
- irrigation;
- weather-related intent.

---

# 7. Context Engine

Agricultural advice is contextual.

The context engine combines:

```text
Farmer Profile
+
Farm Profile
+
Crop Passport
+
Location
+
Crop Stage
+
Weather
+
Conversation History
```

## Crop Passport

Example:

```text
Crop: Soybean
Location: Pune
Sowing date: 18 July
Area: 2 acres
Stage: Vegetative
Irrigation: Rainfed
Season: Kharif
```

The MVP can infer stage approximately from sowing date and ask the farmer to confirm when necessary.

---

# 8. Weather Context

Weather is dynamic, so it should not rely only on static indexed documents.

The system can combine:

- current weather;
- forecast;
- IMD agrometeorological advisories;
- farmer location.

Example decision:

```text
Spraying question
       ↓
Crop + location
       ↓
Current/forecast weather
       ↓
Rain/wind conditions
       ↓
Relevant agricultural advisory
```

Weather context should be used as supporting context, not as a replacement for agricultural authority.

---

# 9. Safety Architecture

## 9.1 Pre-LLM Safety

Runs before generation.

Checks:

- scope;
- high-risk intent;
- missing critical context;
- unsafe request;
- unsupported category;
- evidence availability.

Example:

```text
High-risk pesticide dosage request
        ↓
No authoritative evidence
        ↓
Do not generate recommendation
        ↓
Clarify or escalate
```

---

## 9.2 Grounding Check

After retrieval and before generation:

```text
Is there enough trustworthy evidence?
Is it relevant?
Is it current?
Does it match crop?
Does it match location?
Does it match stage?
Are sources conflicting?
```

If evidence is insufficient, FasalMitra should not manufacture an answer.

---

## 9.3 LLM

The LLM is an **answer-generation/reasoning component**, not the agricultural source of truth.

Prompt structure should include:

- normalized farmer question;
- context;
- retrieved evidence;
- source metadata;
- explicit "use only supplied evidence" constraints;
- response format;
- safety constraints.

---

## 9.4 Post-LLM Safety

Validate the generated response.

Checks include:

- unsupported claims;
- numerical claims;
- dosage/frequency consistency;
- crop consistency;
- location consistency;
- source consistency;
- contradiction with evidence;
- unsafe recommendations.

A claim that cannot be supported should be removed/rejected.

---

# 10. Confidence and Escalation

Do not rely blindly on the LLM's self-reported confidence.

Create a **system-level confidence/grounding score** using observable signals:

```text
Evidence relevance
Source authority
Crop match
Location match
Stage match
Freshness
Cross-source agreement
Claim support
```

Initial policy can be configurable:

```text
HIGH
→ answer

MEDIUM
→ ask clarification / cautious response

LOW
→ expert escalation
```

Thresholds must eventually be calibrated using a held-out evaluation set.

---

# 11. Expert Escalation

When AI should not answer:

```text
Farmer
 ↓
FasalMitra
 ↓
Low grounding / high risk
 ↓
Expert queue
 ↓
Agricultural expert
 ↓
Verified answer
 ↓
Farmer
```

Expert dashboard should show:

- farmer question;
- language;
- location;
- crop;
- crop stage;
- retrieved evidence;
- AI draft, if any;
- confidence;
- reason for escalation;
- conversation history.

This creates a human-in-the-loop safety system.

---

# 12. End-to-End Request Flow

Example:

> Farmer: "Should I spray my soybean tomorrow?"

### Step 1 — Input

Phone/WhatsApp receives audio.

### Step 2 — ASR

Speech becomes text.

### Step 3 — Query Understanding

```text
Intent = spraying_advice
Crop = soybean
Time = tomorrow
```

### Step 4 — Context

Retrieve:

- location;
- crop stage;
- sowing date;
- weather.

### Step 5 — Pre-Safety

Determine whether the request requires high-risk evidence.

### Step 6 — Hybrid Retrieval

Search:

- KVK/ICAR;
- IMD;
- relevant KCC examples;
- metadata-filtered documents.

### Step 7 — Rerank

Prioritize relevant, authoritative, recent evidence.

### Step 8 — Grounding

If evidence is inadequate → clarify/escalate.

### Step 9 — LLM

Generate answer only from supported evidence.

### Step 10 — Post-Safety

Verify every important actionable claim.

### Step 11 — Confidence

High → continue.

Low → expert.

### Step 12 — Translation

Produce the farmer's language.

### Step 13 — TTS

Convert final validated text to speech.

### Step 14 — Delivery

Return audio through phone/WhatsApp.

---

# 13. Suggested Service Boundaries

Start as a modular monolith for the hackathon, with clean internal modules.

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── webhooks/
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── domain/
│   │   ├── farmer/
│   │   ├── crop/
│   │   ├── advisory/
│   │   ├── conversation/
│   │   └── escalation/
│   ├── ai/
│   │   ├── asr/
│   │   ├── query_understanding/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   ├── reranking/
│   │   ├── llm/
│   │   ├── translation/
│   │   ├── tts/
│   │   └── safety/
│   ├── knowledge/
│   │   ├── ingestion/
│   │   ├── parsers/
│   │   ├── chunking/
│   │   └── indexing/
│   ├── weather/
│   └── db/
├── tests/
└── main.py
```

For a hackathon, **do not start with dozens of microservices**. Modular boundaries give us most of the engineering benefit without deployment complexity.

---

# 14. Repository Structure

Recommended top-level repository:

```text
FasalMitra/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── docs/
│   ├── architecture.md
│   ├── data-pipeline.md
│   ├── safety.md
│   ├── retrieval.md
│   └── evaluation.md
│
├── frontend/
│
├── backend/
│
├── ingestion/
│
├── models/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
├── evaluation/
│
└── scripts/
```

Do not commit private datasets, credentials, API keys, or copyrighted source dumps that the repository is not permitted to redistribute.

---

# 15. Initial API Design

Suggested APIs:

```text
POST /api/v1/query
POST /api/v1/voice/query
POST /api/v1/whatsapp/webhook

GET  /api/v1/farmers/{id}
GET  /api/v1/farmers/{id}/crops

POST /api/v1/escalations
GET  /api/v1/escalations

GET  /api/v1/advisories
GET  /api/v1/sources

POST /api/v1/feedback
```

Internal AI pipeline:

```text
POST /internal/asr
POST /internal/query-understanding
POST /internal/retrieve
POST /internal/rerank
POST /internal/generate
POST /internal/validate
POST /internal/translate
POST /internal/tts
```

These internal boundaries can remain Python modules initially rather than separate network services.

---

# 16. Database Concepts

Core tables/entities:

```text
farmers
farms
crop_cycles
crop_observations
conversations
messages
knowledge_sources
knowledge_documents
knowledge_chunks
advisories
retrieval_events
answer_claims
safety_events
escalations
experts
feedback
weather_snapshots
```

Important audit fields:

```text
created_at
updated_at
source_id
document_id
model_version
pipeline_version
request_id
```

For agricultural answers, auditability is a first-class feature.

---

# 17. Observability

Track:

### System metrics

- API latency;
- ASR latency;
- retrieval latency;
- LLM latency;
- TTS latency;
- error rate.

### AI metrics

- ASR WER;
- retrieval recall;
- reranker quality;
- grounded answer rate;
- unsupported claim rate;
- escalation rate;
- clarification rate.

### Product metrics

- successful conversations;
- farmer feedback;
- repeated questions;
- expert resolution rate.

---

# 18. Evaluation Strategy

A production-grade AI system needs a test set.

Create a curated evaluation dataset containing:

```text
Language
Crop
Location
Intent
Question
Expected evidence
Risk level
Expected answer properties
```

Test categories:

1. normal questions;
2. ambiguous questions;
3. multilingual questions;
4. code-switched questions;
5. noisy ASR;
6. outdated advisory conflicts;
7. wrong-location distractors;
8. unsupported questions;
9. high-risk input questions;
10. hallucination/adversarial prompts.

---

# 19. Key Quality Metrics

## Retrieval

- Recall@K
- MRR / nDCG where appropriate

## Answer grounding

- supported claim rate;
- citation/evidence coverage;
- contradiction rate.

## Safety

- unsafe-answer rate;
- false-safe rate;
- escalation precision/recall.

## Voice

- WER;
- language identification accuracy;
- end-to-end latency;
- TTS intelligibility.

The most important safety KPI is:

> **How often does FasalMitra give an actionable answer that is not supported by authoritative evidence?**

Our target should be as close to zero as engineering can make it.

---

# 20. Security and Privacy

Never commit:

- API keys;
- phone numbers from private datasets;
- authentication secrets;
- production database credentials;
- private farmer information.

Use:

```text
.env
.env.example
```

Store only the minimum farmer information required.

Use access control for expert/admin dashboards.

Keep audit logs without exposing unnecessary personal data.

---

# 21. Deployment Strategy

### Development

```text
Docker Compose
├── frontend
├── backend
├── postgres
└── redis
```

### Production direction

```text
Reverse Proxy / Load Balancer
          │
      Frontend
          │
       FastAPI
     ┌────┼─────┐
     │    │     │
 Postgres Redis AI workers
              │
       External AI/Voice APIs
```

AI-heavy workloads such as ingestion, embedding, batch evaluation, and potentially ASR/TTS should be handled asynchronously where appropriate.

---

# 22. Development Roadmap

## Phase 0 — Repository

- initialize Git;
- create README;
- create environment configuration;
- Docker Compose;
- FastAPI skeleton;
- Next.js skeleton.

## Phase 1 — Knowledge

- acquire permitted datasets;
- build ingestion;
- parse documents;
- normalize metadata;
- chunk;
- embed;
- index.

## Phase 2 — RAG

- query understanding;
- hybrid retrieval;
- reranking;
- grounding check;
- source provenance.

## Phase 3 — Safety

- pre-LLM policy;
- risk classifier;
- claim extraction;
- post-LLM validation;
- confidence;
- escalation.

## Phase 4 — Voice

- ASR;
- TTS;
- multilingual pipeline;
- noisy-audio evaluation.

## Phase 5 — Channels

- phone;
- WhatsApp.

## Phase 6 — Personalization

- farmer profile;
- crop passport;
- location;
- weather.

## Phase 7 — Expert system

- expert dashboard;
- escalation queue;
- feedback loop.

## Phase 8 — Production hardening

- observability;
- evaluation;
- security;
- load testing;
- failure recovery.

---

# 23. MVP vs Advanced Features

## Hackathon MVP

Must have:

- one or two Indian languages;
- voice input;
- ASR;
- agricultural RAG;
- ICAR/KVK evidence;
- hybrid retrieval;
- reranking;
- grounding;
- safety checks;
- TTS;
- source provenance;
- expert escalation.

## Advanced

Add:

- more languages;
- WhatsApp;
- weather personalization;
- crop passport;
- multilingual KCC semantic search;
- automatic crop-stage estimation;
- image-based crop symptom input;
- continuous expert feedback;
- offline/edge capabilities;
- advanced analytics.

---

# 24. What Makes FasalMitra Different

Do not pitch it as:

> "An AI chatbot for farmers."

Pitch it as:

> **"A safety-first, voice-native agricultural evidence engine that retrieves localized ICAR/KVK/IMD knowledge, understands Indian-language farmer speech, validates every actionable response, and escalates uncertain cases to humans."**

The differentiator is not simply the LLM.

It is the **grounded decision pipeline**.

---

# 25. Engineering Rules We Should Never Break

1. **Never invent agronomic advice.**
2. **Never treat LLM memory as authoritative agricultural knowledge.**
3. **Never bypass grounding for convenience.**
4. **Never use a stale or wrong-location advisory without detecting it.**
5. **Never silently ignore source conflicts.**
6. **Never expose unsupported dosage/chemical recommendations.**
7. **Never hide uncertainty from the farmer.**
8. **Always maintain source provenance.**
9. **Always log the pipeline/model version for important answers.**
10. **Escalation is a feature, not a failure.**

---

# 26. Final Mental Model

```text
                 FASALMITRA
                     │
        ┌────────────┼────────────┐
        │            │            │
     INTERACTION   INTELLIGENCE  KNOWLEDGE
        │            │            │
    Phone/WA       Query         ICAR
       ASR         Context       KVK
       TTS         Retrieval     KCC
                   Reranker      IMD
                   LLM
                     │
                  SAFETY
                     │
              ┌──────┴──────┐
              │             │
           Answer        Expert
              │
          Translation
              │
             TTS
              │
           Farmer
```

**FasalMitra = Voice + Indian Languages + Agricultural Knowledge + Retrieval + Safety + Human Escalation.**

This is the baseline architecture we should implement against.
