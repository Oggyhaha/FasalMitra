import asyncio
from backend.app.api.advisory import process_advisory_query
from backend.app.schemas.schemas import AdvisoryQueryRequest
from backend.app.db.database import SessionLocal

async def test():
    db = SessionLocal()
    try:
        tests = [
            ("Market price Gujarat", "en", "What is the market price of cotton in Gujarat?"),
            ("KCC data", "en", "What are the common crop diseases in Bihar?"),
            ("Crop info", "en", "Tell me about wheat cultivation"),
        ]
        for name, lang, text in tests:
            req = AdvisoryQueryRequest(
                farmer_id='FARM-1001',
                channel='WEB_SIMULATOR',
                language=lang,
                text=text,
                crop_override='General',
                crop_stage_days=0,
                location_district='Latur',
                location_state='Maharashtra'
            )
            result = await process_advisory_query(req, db)
            print(f'\n=== {name} ===')
            print(f'Status: {result.status}')
            print(f'Confidence: {result.confidence_score:.2f}')
            print(f'Grounding: {result.grounding_status}')
            safe_ans = ''.join([c if ord(c) < 128 else '?' for c in result.answer_text[:200]])
            print(f'Answer: {safe_ans}...')
    finally:
        db.close()

asyncio.run(test())