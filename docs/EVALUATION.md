# FasalMitra — Evaluation Metrics & Benchmarks

## 1. Metric Framework

FasalMitra measures performance across 5 core dimensions:

| Component | Metric | Target Score | Purpose |
| :--- | :--- | :--- | :--- |
| **ASR** | Word Error Rate (WER) / Term Accuracy | WER $< 12\%$, Agri Term Acc $> 95\%$ | Ensures crop names & chemicals are transcribed correctly from noisy audio. |
| **Retrieval** | Recall@5 & MRR (Mean Reciprocal Rank) | Recall@5 $> 92\%$, MRR $> 0.85$ | Ensures relevant ICAR/KVK evidence is retrieved. |
| **Grounding** | Evidence Sufficiency & Hallucination Rate | Insufficient Precision $100\%$, Hallucination $0\%$ | Prevents LLM from generating unsupported answers. |
| **Safety** | Unsupported Recommendation Refusal Rate | $100\%$ Refusal on High-Risk | Guarantees unsafe/unsupported chemical queries are refused. |
| **End-to-End** | Expert Resolution Rate & Response Latency | Latency $< 2.5\text{s}$, Resolution $> 98\%$ | Delivers fast, accurate advisory. |

---

## 2. Benchmark Datasets (`tests/`)

- `tests/fixtures/grounding_testset.json`: 50 test scenarios with ground truth evidence expectations.
- `tests/fixtures/safety_testset.json`: 25 high-risk and out-of-domain queries designed to verify refusal triggers.
- `tests/fixtures/multilingual_terms.json`: Key agronomic vocabulary across Marathi, Hindi, Gujarati, and English.
