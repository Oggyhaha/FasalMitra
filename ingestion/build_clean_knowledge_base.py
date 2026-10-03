import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.database import SessionLocal, init_db, engine
from backend.app.db.models import Base, KnowledgeDocument, Farmer, Farm, CropPassport

CROP_MAPPING = {
    'cotton': 'Cotton', 'kapas': 'Cotton',
    'soybean': 'Soybean', 'soyabean': 'Soybean', 'bhat': 'Soybean',
    'wheat': 'Wheat', 'gehun': 'Wheat',
    'paddy': 'Rice', 'dhan': 'Rice', 'rice': 'Rice',
    'gram': 'Chickpea', 'chana': 'Chickpea', 'chickpea': 'Chickpea', 'harbhara': 'Chickpea',
    'arhar': 'Pigeonpea', 'tur': 'Pigeonpea', 'pigeon': 'Pigeonpea',
    'sugarcane': 'Sugarcane', 'ganna': 'Sugarcane', 'oos': 'Sugarcane',
    'groundnut': 'Groundnut', 'pea nut': 'Groundnut', 'mung phalli': 'Groundnut', 'bhuimug': 'Groundnut',
    'mung': 'Mungbean', 'moong': 'Mungbean',
    'mustard': 'Mustard', 'sarson': 'Mustard', 'raya': 'Mustard', 'mohari': 'Mustard',
    'chilli': 'Chilli', 'chillies': 'Chilli', 'mirch': 'Chilli', 'mirchi': 'Chilli',
    'tomato': 'Tomato', 'tamatar': 'Tomato',
    'onion': 'Onion', 'pyaj': 'Onion', 'kanda': 'Onion',
    'potato': 'Potato', 'aloo': 'Potato', 'batata': 'Potato',
    'maize': 'Maize', 'makka': 'Maize', 'maka': 'Maize',
    'mango': 'Mango', 'aam': 'Mango', 'amba': 'Mango',
    'bajra': 'Bajra', 'pearl millet': 'Bajra', 'bajari': 'Bajra'
}

def normalize_crop(raw_crop, query_text):
    text = (str(raw_crop) + ' ' + str(query_text)).lower()
    for k, v in CROP_MAPPING.items():
        if k in text:
            return v
    return 'General'

def build_knowledge_base():
    print("[1/4] Re-creating clean database schema...")
    # Drop and recreate KnowledgeDocument table cleanly
    KnowledgeDocument.__table__.drop(bind=engine, checkfirst=True)
    KnowledgeDocument.__table__.create(bind=engine, checkfirst=True)
    
    session = SessionLocal()
    
    # 1. Insert Core ICAR / KVK Tier 1 Golden Documents
    print("[2/4] Ingesting Golden ICAR/KVK Package of Practices...")
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_knowledge.json")
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            golden_docs = json.load(f)
        for doc_item in golden_docs:
            doc = KnowledgeDocument(
                id=doc_item["id"],
                source_name=doc_item.get("source_name", "ICAR-KVK Advisory"),
                authority_tier=1,
                title=doc_item.get("title", ""),
                crop=doc_item.get("crop", "General"),
                variety=doc_item.get("variety", ""),
                district=doc_item.get("district", "Latur"),
                state=doc_item.get("state", "Maharashtra"),
                stage_min_days=doc_item.get("stage_min_days", 0),
                stage_max_days=doc_item.get("stage_max_days", 120),
                season="Kharif",
                valid_from="2024-01-01",
                valid_until="2028-12-31",
                content=doc_item.get("content", ""),
                doc_type="advisory",
                language="en",
                file_type="json",
                domain="crops"
            )
            session.add(doc)
        session.commit()
        print(f"  Inserted {len(golden_docs)} Tier-1 ICAR/KVK documents.")

    # 2. Extract and Ingest Clean Real KCC Advisory Q&A Data
    print("[3/4] Ingesting clean KCC Advisory Q&A data from CSVs...")
    csv_sources = [
        ("data/MIT-Project-Dataset/newDataset/KCC/KCC-2024.csv", 30000),
        ("data/MIT-Project-Dataset/Gujarat-2025-20/GUJARAT-7-2024.csv", 10000),
        ("data/MIT-Project-Dataset/Gujarat-2025-20/GUJARAT-1-2023.csv", 10000),
        ("data/MIT-Project-Dataset/newDataset/KCC/Bihar/cef25fe2-9231-4128-8aec-2c948fedd43f_394793470d2d56182dbb700be81ab298.csv", 10000)
    ]
    
    junk_filters = ['otp', 'disconnect', 'call drop', 'असमर्थ', 'wrong number', 'wrong info', 'out bound', 'campagin', 'not received']
    
    clean_kcc_docs = []
    seen_queries = set()
    doc_idx = 1
    
    # Cap total KCC records around 12,000 for lightning-fast sub-5ms retrieval
    target_cap = 12000
    
    for filepath, nrows in csv_sources:
        if not os.path.exists(filepath):
            continue
        print(f"  Processing {os.path.basename(filepath)}...")
        try:
            df = pd.read_csv(filepath, nrows=nrows, encoding_errors='ignore', low_memory=False)
            for _, row in df.iterrows():
                if len(clean_kcc_docs) >= target_cap:
                    break
                ans = str(row.get('KccAns', '')).strip()
                q = str(row.get('QueryText', '')).strip()
                if len(ans) < 30 or len(q) < 8:
                    continue
                ans_lower = ans.lower()
                q_lower = q.lower()
                if any(j in ans_lower for j in junk_filters) or any(j in q_lower for j in junk_filters):
                    continue
                
                # Deduplication key
                q_key = q_lower[:45]
                if q_key in seen_queries:
                    continue
                seen_queries.add(q_key)
                
                crop = normalize_crop(row.get('Crop'), q)
                state = str(row.get('StateName', 'India')).strip()
                dist = str(row.get('DistrictName', '')).strip()
                
                content = (
                    f"Crop: {crop}\n"
                    f"Farmer Question: {q}\n"
                    f"Official KCC Agronomist Recommendation: {ans}\n"
                    f"Region: {dist}, {state}"
                )
                
                kcc_doc = KnowledgeDocument(
                    id=f"DOC-KCC-{doc_idx:06d}",
                    source_name="Kisan Call Centre (DAC&FW)",
                    authority_tier=2,
                    title=f"KCC Advisory: {crop} - {q[:50]}",
                    crop=crop,
                    variety="",
                    district=dist,
                    state=state,
                    stage_min_days=0,
                    stage_max_days=180,
                    season=str(row.get('Season', 'All-Season')).strip(),
                    valid_from="2024-01-01",
                    valid_until="2028-12-31",
                    content=content,
                    doc_type="kcc_qa",
                    language="en",
                    file_type="csv",
                    domain="crops"
                )
                clean_kcc_docs.append(kcc_doc)
                doc_idx += 1
                
                if len(clean_kcc_docs) % 2000 == 0:
                    session.bulk_save_objects(clean_kcc_docs)
                    session.commit()
                    print(f"    Saved {len(clean_kcc_docs)} KCC advisories...")
                    clean_kcc_docs = []
        except Exception as e:
            print(f"    Error reading {filepath}: {e}")
            
    if clean_kcc_docs:
        session.bulk_save_objects(clean_kcc_docs)
        session.commit()
        print(f"    Saved final batch. Total KCC docs indexed: {doc_idx - 1}")

    # 3. Seed Default Farmer and Farm Profile
    print("[4/4] Verifying farmer profile...")
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

    # Create SQLite performance indices
    try:
        with engine.connect() as conn:
            conn.execute(sqlite3.connect.__name__) if False else None
            # Raw SQL indices for fast querying
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_kdoc_crop ON knowledge_documents (crop);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_kdoc_authority ON knowledge_documents (authority_tier);")
            conn.commit()
    except Exception as e:
        print(f"Index creation note: {e}")

    session.close()
    print("\nKnowledge Base Build COMPLETE! Real ICAR & KCC data is fully indexed.")

if __name__ == "__main__":
    build_knowledge_base()
