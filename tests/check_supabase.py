import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect
from backend.app.db.database import engine, init_db, SessionLocal
from backend.app.db.models import KnowledgeDocument, Farmer, Farm, CropPassport

def check_db():
    print(f"Connecting to Database URL: {engine.url}")
    try:
        init_db()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ SUCCESSFULLY CONNECTED TO SUPABASE CLOUD!")
        print(f"📋 Found Tables in Supabase Database ({len(tables)}): {tables}")

        session = SessionLocal()
        try:
            docs_count = session.query(KnowledgeDocument).count()
            farmers_count = session.query(Farmer).count()
            farms_count = session.query(Farm).count()
            passports_count = session.query(CropPassport).count()

            print(f"📊 LIVE SUPABASE RECORD METRICS:")
            print(f"   • Knowledge Documents: {docs_count} records")
            print(f"   • Farmers: {farmers_count} records")
            print(f"   • Farms: {farms_count} records")
            print(f"   • Crop Passports: {passports_count} records")
        finally:
            session.close()

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_db()
