# FasalMitra — API Specifications

## 1. REST Endpoints Overview

### 1.1 Advisory Pipeline API

#### `POST /api/v1/advisory/query`
Executes the full FasalMitra advisory pipeline for text or voice inputs.

**Request Payload:**
```json
{
  "farmer_id": "FARM-1002",
  "channel": "PHONE", // "PHONE", "WHATSAPP", "WEB_SIMULATOR"
  "language": "mr", // "hi", "mr", "gu", "en", "auto"
  "text": "माझ्या सोयाबीनची पाने पिवळी पडत आहेत, मी काय करू?",
  "audio_base64": null,
  "crop_override": "Soybean",
  "crop_stage_days": 35,
  "location_district": "Latur",
  "location_state": "Maharashtra"
}
```

**Response Payload:**
```json
{
  "query_id": "QRY-2026-9812",
  "status": "ANSWERED", // "ANSWERED", "CLARIFICATION_REQUIRED", "ESCALATED_TO_EXPERT"
  "language_detected": "mr",
  "structured_query": {
    "intent": "PEST_DISEASE",
    "crop": "Soybean",
    "symptoms": ["yellowing leaves"],
    "urgency": "MEDIUM"
  },
  "answer_text": "सोयाबीन पानांतील पिवळेपणा पिवळा मोझॅक किंवा पोषक तत्वांच्या कमतरतेमुळे असू शकतो...",
  "audio_url": "/api/v1/voice/audio/QRY-2026-9812.mp3",
  "confidence_score": 0.92,
  "confidence_level": "HIGH",
  "grounding_status": "SUPPORTED",
  "safety_status": "PASSED",
  "retrieved_evidence": [
    {
      "source_id": "KVK-LATUR-2025-04",
      "authority": "KVK",
      "title": "Soybean Yellow Mosaic Advisory",
      "score": 0.89,
      "text": "For yellowing in 30-40 day old soybean, check for whitefly infestation..."
    }
  ],
  "claims_verified": [
    {
      "claim": "Check for whitefly transmission",
      "verified": true
    }
  ],
  "escalation": null
}
```

---

### 1.2 Expert Escalation API

#### `GET /api/v1/expert/escalations`
Retrieves queued escalations requiring human review.

**Query Parameters:**
- `status` (`OPEN`, `RESOLVED`, `ALL`)
- `risk_level` (`HIGH`, `MEDIUM`, `LOW`)

#### `POST /api/v1/expert/escalations/{case_id}/respond`
Submits a verified human expert answer.

**Request Payload:**
```json
{
  "expert_id": "EXP-88",
  "action": "ANSWER", // "ANSWER", "REQUEST_INFO", "ESCALATE_SPECIALIST"
  "verified_answer": "Recommended application of 0.5ml/L Thiamethoxam 25% WG after inspection.",
  "notes": "Verified evidence match with KVK Latur bulletin."
}
```

---

### 1.3 Knowledge & Ingestion API

#### `POST /api/v1/ingestion/upload`
Uploads and indexes new advisory documents (ICAR/KVK/IMD bulletins).

#### `GET /api/v1/admin/sources`
Lists indexed knowledge sources with document counts and freshness status.

---

### 1.4 Webhook Endpoints

#### `POST /api/v1/webhooks/whatsapp`
Handles incoming WhatsApp messages/audio from Twilio or WhatsApp Business API.

#### `POST /api/v1/webhooks/phone`
Handles incoming Voice IVR calls from phone gateway.
