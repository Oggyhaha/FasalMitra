import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models import KnowledgeDocument, Farmer, Farm, CropPassport

def seed_database():
    print("Initializing Database...")
    init_db()

    session = SessionLocal()
    try:
        # 1. Seed Sample Documents
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_knowledge.json")
        with open(data_path, "r", encoding="utf-8") as f:
            docs_data = json.load(f)

        for doc_item in docs_data:
            existing = session.get(KnowledgeDocument, doc_item["id"])
            if existing:
                existing.source_name = doc_item["source_name"]
                existing.authority_tier = doc_item["authority_tier"]
                existing.title = doc_item["title"]
                existing.crop = doc_item["crop"]
                existing.district = doc_item["district"]
                existing.state = doc_item["state"]
                existing.content = doc_item["content"]
            else:
                doc = KnowledgeDocument(
                    id=doc_id if 'doc_id' in locals() else doc_item["id"],
                    source_name=doc_item["source_name"],
                    authority_tier=doc_item["authority_tier"],
                    title=doc_item["title"],
                    crop=doc_item["crop"],
                    district=doc_item["district"],
                    state=doc_item["state"],
                    content=doc_item["content"]
                )
                session.add(doc)

        # 2. Seed Default Farmer Profile
        farmer = session.get(Farmer, "FARM-1001")
        if not farmer:
            farmer = Farmer(
                id="FARM-1001",
                name="Ramesh Patil",
                phone_number="+91 98230 12345",
                preferred_language="mr",
                state="Maharashtra",
                district="Latur"
            )
            session.add(farmer)
            
            farm = Farm(
                id="FARM-MAINT-01",
                farmer_id="FARM-1001",
                farm_name="Latur Farm",
                area_acres=4.0,
                soil_type="Black Cotton Soil",
                district="Latur",
                state="Maharashtra"
            )
            session.add(farm)
            
            passport = CropPassport(
                id="CROP-SOY-01",
                farm_id="FARM-MAINT-01",
                crop_name="Soybean",
                variety="JS 335",
                sowing_date="2026-06-15",
                stage_days=35,
                season="Kharif"
            )
            session.add(passport)

        session.commit()
        print("Database Seeding Completed Successfully!")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
