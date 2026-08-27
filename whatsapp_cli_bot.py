import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.schemas.schemas import AdvisoryQueryRequest
from backend.app.api.advisory import process_advisory_query
from backend.app.db.database import SessionLocal, init_db

async def run_whatsapp_cli_bot():
    print("=" * 70)
    print("🌾 FASALMITRA — OFFICIAL WHATSAPP & VOICE AI ASSISTANT (CLI BOT)")
    print("   Grounded in ICAR/KVK Package-of-Practices & IMD Agromet Data")
    print("=" * 70)
    print("Commands:")
    print("  • Type any crop question (e.g. 'माझ्या सोयाबीनची पाने पिवळी पडत आहेत')")
    print("  • Type '/weather' for IMD Agromet forecast")
    print("  • Type '/passport' for Farmer Crop Passport")
    print("  • Type '/expert' for Expert Escalation status")
    print("  • Type 'exit' or 'quit' to stop")
    print("-" * 70)

    db = SessionLocal()
    try:
        init_db()
        while True:
            try:
                user_input = input("\n📱 Farmer [WhatsApp] > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting FasalMitra WhatsApp Bot. Goodbye!")
                    break

                # Process via Webhook / Advisory Pipeline
                advisory_req = AdvisoryQueryRequest(
                    farmer_id="FARM-1001",
                    channel="WHATSAPP",
                    language="auto",
                    text=user_input,
                    location_district="Latur",
                    location_state="Maharashtra"
                )

                print("⏳ Processing through 14-Stage Grounding Pipeline...")
                res = await process_advisory_query(advisory_req, db)

                grounding_badge = "✅ ICAR/KVK Grounded Evidence" if res.grounding_status == "SUPPORTED" else "⚠️ Escalated to Expert Queue"
                evidence_source = res.retrieved_evidence[0].title if res.retrieved_evidence else "ICAR/KVK Advisory"

                print("\n" + "=" * 50)
                print(f"🌾 [FasalMitra Grounded Advisory Response]")
                print("=" * 50)
                print(res.answer_text)
                print("\n📌 Metadata & Provenance:")
                print(f"   • Confidence Score: {int(res.confidence_score * 100)}% ({res.confidence_level})")
                print(f"   • Grounding Status: {grounding_badge}")
                print(f"   • Evidence Source:  {evidence_source}")
                if res.audio_url:
                    print(f"   • Voice Audio TTS:  {res.audio_url}")
                print("=" * 50)

            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except Exception as e:
                print(f"Error: {e}")
    finally:
        session = db.close()

if __name__ == "__main__":
    asyncio.run(run_whatsapp_cli_bot())
