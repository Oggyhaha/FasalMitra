# FasalMitra — Safety & Grounding Specification

## 1. Safety Principles & Risk Taxonomy

FasalMitra categorizes queries into three risk tiers:

| Risk Tier | Query Types | Evidence Requirement | Validation Rule |
| :--- | :--- | :--- | :--- |
| **LOW** | General agricultural practices, crop lifecycle information, weather updates. | 1+ verified source candidate. | General semantic grounding check. |
| **MEDIUM** | Crop disease identification, pest infestation guidance, fertilizer schedules. | 2+ consistent authoritative advisories (KVK/ICAR). | Grounding check + LLM claim verification. |
| **HIGH** | Chemical spraying recommendations, specific pesticide dosages, tank mixes. | 100% exact match in localized KVK advisory with explicit dosage & crop stage. | Mandatory pre-safety check + claim verification + confidence $\ge 0.85$. Escalates if missing exact stage. |

---

## 2. Pre-LLM Safety Gate (`backend/app/core/safety_gate.py`)

Before any prompt is constructed for an LLM, the request passes through the **Pre-Safety Gate**:

1. **Out-of-Domain Filter:** Rejects non-agricultural topics (coding, politics, general chat).
2. **Hazardous Chemical Mix Check:** Rejects requests asking to combine incompatible or banned chemicals.
3. **Missing Context Refusal:** If a query requests chemical dosage without specifying crop stage or pest severity, the system refuses to guess and triggers a clarification question.
4. **Unsupported High-Risk Action:** If no authoritative document exists for the exact chemical/crop combination, LLM execution is blocked.

---

## 3. Grounding Gate (`backend/app/core/grounding_gate.py`)

The Grounding Gate evaluates the candidate evidence retrieved by the Hybrid Retriever:

```text
                  Retrieved Candidates
                           │
                           ▼
          ┌──────────────────────────────────┐
          │  Metadata Alignment Matrix Check │
          │  - Crop Match?                   │
          │  - District / State Match?       │
          │  - Freshness (Not Expired)?      │
          └────────────────┬─────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [ Matrix Satisfied ]        [ Matrix Failed ]
             │                           │
             ▼                           ▼
  Evaluate Evidence Content    Status = INSUFFICIENT / STALE
             │                           │
    ┌────────┴────────┐                  ▼
    ▼                 ▼           [ Trigger Escalation ]
[Sufficient]    [Conflicting]
    │                 │
    ▼                 ▼
Status =        Status = CONFLICTING
SUPPORTED            │
                     ▼
              [ Trigger Escalation ]
```

---

## 4. Post-LLM Claim Extraction & Verification (`backend/app/core/claim_verifier.py`)

After the LLM generates a response, the **Claim Verifier** runs post-validation:

1. **Claim Extraction:** Parses out dosage numbers (e.g. `2 ml/liter`), chemical names (`Thiamethoxam`), unit sizes (`acre`), and timing (`after 4 PM`).
2. **Evidence Substring Match:** Verifies each extracted claim against the raw text of the retrieved documents.
3. **Rejection Rule:** If any quantitative claim in the generated text lacks empirical support in the retrieved evidence:
   - Generated answer is REJECTED.
   - Case is queued for Expert Escalation with reason `UNSUPPORTED_CLAIM_GENERATED`.
