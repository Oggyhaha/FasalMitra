import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models import KnowledgeDocument, Farmer, Farm, CropPassport


def seed_database(jsonl_path: str = None):
    print("Initializing Database...")
    init_db()

    session = SessionLocal()
    try:
        if jsonl_path and os.path.exists(jsonl_path):
            print(f"Loading from: {jsonl_path}")
            docs_data = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        chunk = json.loads(line)
                        doc_data = {
                            "id": chunk.get("chunk_id", f"DOC-UNIV-{len(docs_data):06d}"),
                            "source_name": chunk.get("source_file", "Universal Import"),
                            "authority_tier": chunk.get("authority_tier", 3),
                            "title": chunk.get("title", chunk.get("source_file", "Imported")),
                            "crop": chunk.get("crop", chunk.get("domain", "General")),
                            "variety": chunk.get("subdomain", chunk.get("variety", "")),
                            "district": chunk.get("metadata", {}).get("district", ""),
                            "state": chunk.get("metadata", {}).get("state", ""),
                            "stage_min_days": chunk.get("metadata", {}).get("stage_min_days", 0),
                            "stage_max_days": chunk.get("metadata", {}).get("stage_max_days", 120),
                            "season": chunk.get("metadata", {}).get("season", "Kharif"),
                            "valid_from": chunk.get("metadata", {}).get("valid_from", "2024-01-01"),
                            "valid_until": chunk.get("metadata", {}).get("valid_until", "2028-12-31"),
                            "content": chunk.get("content", ""),
                            "doc_type": chunk.get("doc_type", "universal"),
                            "language": chunk.get("language", "en"),
                            "file_type": chunk.get("file_type", ""),
                            "entities": chunk.get("entities", {}),
                            "source_path": chunk.get("source_path", ""),
                            "domain": chunk.get("domain", "crops"),
                            "subdomain": chunk.get("subdomain", ""),
                        }
                        docs_data.append(doc_data)
            print(f"Loaded {len(docs_data)} chunks")
        else:
            data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_knowledge.json")
            with open(data_path, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
            print(f"Loaded {len(docs_data)} default documents")

        for doc_item in docs_data:
            existing = session.get(KnowledgeDocument, doc_item["id"])
            if existing:
                for key, val in doc_item.items():
                    if hasattr(existing, key):
                        setattr(existing, key, val)
            else:
                # Filter to only model fields
                model_fields = {k: v for k, v in doc_item.items() if hasattr(KnowledgeDocument, k)}
                doc = KnowledgeDocument(**model_fields)
                session.add(doc)

        # Seed default farmer
        farmer = session.get(Farmer, "FARM-1001")
        if not farmer:
            farmer = Farmer(id="FARM-1001", name="Ramesh Patil", phone_number="+91 98230 12345",
                          preferred_language="mr", state="Maharashtra", district="Latur")
            session.add(farmer)
            farm = Farm(id="FARM-MAINT-01", farmer_id="FARM-1001", farm_name="Latur Farm",
                       area_acres=4.0, soil_type="Black Cotton Soil", district="Latur", state="Maharashtra")
            session.add(farm)
            passport = CropPassport(id="CROP-SOY-01", farm_id="FARM-MAINT-01", crop_name="Soybean",
                                   variety="JS 335", sowing_date="2026-06-15", stage_days=35, season="Kharif")
            session.add(passport)

        session.commit()
        print("Database Seeding Completed!")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="Path to reviewed JSONL")
    args = parser.parse_args()
    seed_database(args.source)