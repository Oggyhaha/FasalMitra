import asyncio
from backend.app.api.advisory import process_advisory_query
from backend.app.schemas.schemas import AdvisoryQueryRequest
from backend.app.db.database import SessionLocal
from backend.app.core.retrieval_engine import retrieval_engine
from backend.app.core.query_understanding import query_understanding_engine
from backend.app.core.grounding_gate import grounding_gate
from backend.app.core.safety_gate import pre_safety_gate
from backend.app.core.claim_verifier import claim_verifier

async def test_pipeline_components():
    db = SessionLocal()
    print("=" * 60)
    print("TESTING INDIVIDUAL PIPELINE COMPONENTS")
    print("=" * 60)
    
    # 1. Query Understanding
    print("\n1. QUERY UNDERSTANDING")
    test_queries = [
        "My cotton has pink bollworm, what spray?",
        "Wheat price in Gujarat market today",
        "Government subsidy for drip irrigation",
        "Soybean yellow mosaic virus treatment",
        "When to sow rice in Kharif",
    ]
    for q in test_queries:
        nlp = query_understanding_engine.parse_query(q)
        print(f"  '{q[:40]}...' -> intent={nlp['intent']}, crop={nlp['crop']}, symptoms={nlp['symptoms']}")
    
    # 2. Safety Gate
    print("\n2. PRE-SAFETY GATE")
    safety_tests = [
        ("Normal query", "Cotton pest control"),
        ("Banned chemical", "Spray monocrotophos on wheat"),
        ("Out of domain", "Bitcoin price prediction"),
    ]
    for name, q in safety_tests:
        nlp = query_understanding_engine.parse_query(q)
        passed, risk, reason = pre_safety_gate.evaluate(q, nlp, {"crop": "General"})
        print(f"  {name}: passed={passed}, risk={risk}, reason={reason}")
    
    # 3. Retrieval
    print("\n3. RETRIEVAL ENGINE")
    retrieval_tests = [
        ("cotton pest", "Cotton", "Nagpur"),
        ("wheat price", "Wheat", "Ahmedabad"),
        ("soybean disease", "Soybean", "Latur"),
    ]
    for query, crop, district in retrieval_tests:
        results = retrieval_engine.retrieve(db, query, crop, district, top_k=3)
        print(f"  '{query}' -> {len(results)} chunks, top_score={results[0].score if results else 0:.2f}")
    
    # 4. Grounding Gate
    print("\n4. GROUNDING GATE")
    from backend.app.schemas.schemas import EvidenceChunk
    test_evidence = [
        EvidenceChunk(source_id="test", authority="KVK", title="Test", score=0.85, text="Spray Thiamethoxam 100g/ha for pink bollworm"),
    ]
    status, reason = grounding_gate.evaluate_grounding(test_evidence, "PEST_DISEASE", "MEDIUM")
    print(f"  Sufficient evidence: {status} ({reason})")
    
    low_evidence = [
        EvidenceChunk(source_id="test", authority="KVK", title="Test", score=0.25, text="Some general info"),
    ]
    status2, reason2 = grounding_gate.evaluate_grounding(low_evidence, "PEST_DISEASE", "MEDIUM")
    print(f"  Insufficient evidence: {status2} ({reason2})")
    
    # 5. Claim Verification
    print("\n5. CLAIM VERIFICATION")
    evidence = [EvidenceChunk(source_id="t", authority="KVK", title="T", score=0.9, text="Apply 100g/ha Thiamethoxam for pink bollworm")]
    claims, passed = claim_verifier.verify_claims("Spray 100g/ha Thiamethoxam", evidence)
    print(f"  Correct claim: passed={passed}, claims={claims}")
    
    claims2, passed2 = claim_verifier.verify_claims("Spray 500g/ha Thiamethoxam", evidence)
    print(f"  Wrong dosage: passed={passed2}, claims={claims2}")
    
    # 6. Full Pipeline Tests
    print("\n6. FULL PIPELINE TESTS")
    pipeline_tests = [
        ("Crop disease", "mr", "कपासमध्ये गुलाबी इल्ली आहे, मी काय स्प्रे करावे?", "Cotton", 50, "Nagpur", "Maharashtra"),
        ("Market price", "en", "What is the current price of cotton in Gujarat?", "General", 0, "Ahmedabad", "Gujarat"),
        ("Scheme info", "hi", "प्रधानमंत्री किसान सम्मान निधि योजना क्या है?", "General", 0, "Latur", "Maharashtra"),
        ("Weather", "en", "Rain forecast for Latur next week", "General", 0, "Latur", "Maharashtra"),
        ("Fertilizer", "mr", "सोयाबीनसाठी खत कसे द्यावे?", "Soybean", 35, "Latur", "Maharashtra"),
    ]
    
    for name, lang, text, crop, stage, dist, state in pipeline_tests:
        req = AdvisoryQueryRequest(
            farmer_id='FARM-1001', channel='WEB_SIMULATOR', language=lang, text=text,
            crop_override=crop, crop_stage_days=stage, location_district=dist, location_state=state
        )
        result = await process_advisory_query(req, db)
        print(f"\n  {name} ({lang}):")
        print(f"    Status: {result.status} | Conf: {result.confidence_score:.2f} | Ground: {result.grounding_status}")
        safe_ans = ''.join([c if ord(c) < 128 else '?' for c in result.answer_text[:150]])
        print(f"    Answer: {safe_ans}...")
    
    # 7. Database Stats
    print("\n7. DATABASE STATS")
    from backend.app.db.models import KnowledgeDocument, Farmer, Conversation, Escalation
    print(f"  Knowledge docs: {db.query(KnowledgeDocument).count()}")
    print(f"  Farmers: {db.query(Farmer).count()}")
    print(f"  Conversations: {db.query(Conversation).count()}")
    print(f"  Escalations: {db.query(Escalation).count()}")
    
    # Domain distribution
    from sqlalchemy import func
    domains = db.query(KnowledgeDocument.domain, func.count(KnowledgeDocument.id)).group_by(KnowledgeDocument.domain).all()
    for d, c in domains:
        print(f"  Domain '{d}': {c} docs")
    
    db.close()
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

asyncio.run(test_pipeline_components())