#!/usr/bin/env python3
"""
PDF Ingestion Pipeline for FasalMitra
Extracts, chunks, and enriches agricultural PDFs for knowledge base.
Usage: python ingestion/pdf_ingest.py --input /path/to/pdfs --output ./chunks.jsonl
"""

import os
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    os.system("pip install pdfplumber -q")
    import pdfplumber

try:
    from langdetect import detect, LangDetectException
except ImportError:
    print("Installing langdetect...")
    os.system("pip install langdetect -q")
    from langdetect import detect, LangDetectException

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.query_understanding import query_understanding_engine


# ============================================================
# Data Classes
# ============================================================

@dataclass
class PDFChunk:
    chunk_id: str
    source_file: str
    source_path: str
    page_numbers: List[int]
    doc_type: str  # advisory, textbook, thesis, extension
    authority_tier: int  # 1-5
    language: str  # en, mr, hi, gu, mixed
    crop: str
    variety: str
    stage_min_days: int
    stage_max_days: int
    district: str
    state: str
    season: str
    valid_from: str
    valid_until: str
    text: str
    entities: Dict[str, Any]
    extracted_at: str


# ============================================================
# Configuration
# ============================================================

CROP_KEYWORDS = {
    "rice": ["rice", "paddy", "धान", "चावल", "भात", "ప 전화"],
    "wheat": ["wheat", "गेहूं", "गहू", "కంటి"],
    "cotton": ["cotton", "कपास", "कापूस", "పత్తి"],
    "soybean": ["soybean", "सोयाबीन", "सोयाबिन"],
    "sugarcane": ["sugarcane", "गन्ना", "ऊस"],
    "chickpea": ["chickpea", "gram", "चना", "हरभरा", "బ కార్యకర్త"],
    "maize": ["maize", "corn", "मक्का", "మొక్కజొన్న"],
    "mustard": ["mustard", "सरसों", "मोहरी"],
    "groundnut": ["groundnut", "peanut", "मूंगफली", "भुईमुग"],
    "sorghum": ["sorghum", "jowar", "ज्वार", "ज्वारी"],
    "pearl_millet": ["pearl millet", "bajra", "बाजरा", "बाजरी"],
    "finger_millet": ["finger millet", "ragi", "रागी"],
    "barley": ["barley", "जौ"],
    "pigeonpea": ["pigeonpea", "arhar", "tur", "अरहर", "तुवर"],
    "greengram": ["greengram", "moong", "मूंग", "हरी मूंग"],
    "blackgram": ["blackgram", "urad", "उड़द", "काली उड़द"],
}

PEST_DISEASE_KEYWORDS = {
    "blast": ["blast", "ब्लास्ट", "ब्लास्ट रोग", "rice blast", "भात ब्लास्ट", "धान ब्लास्ट"],
    "blight": ["blight", "ब्लाइट", "झुलसा"],
    "rust": ["rust", "रस्ट", "गेरुआ", "तांबेरा", "पीला रतुआ", "पिवळा रतुआ"],
    "wilt": ["wilt", "विल्ट", "उबाळणी", "मुरझाना", "उकटा"],
    "smut": ["smut", "स्मट", "कजली", "कंगारू"],
    "bunt": ["bunt", "बंट", "कंडुवा"],
    "mosaic": ["mosaic", "मोजैक", "मोझॅक", "पीला मोजैक"],
    "bollworm": ["bollworm", "बॉलवर्म", "अळी", "इल्ली", "गुलाबी इल्ली", "गुलाबी अळी", "pink bollworm"],
    "stem_borer": ["stem borer", "स्टेम बोरर", "तना छेदक", "कांदा बोरर"],
    "leaf_folder": ["leaf folder", "लीफ फोल्डर", "पत्ता मोड़क"],
    "whitefly": ["whitefly", "व्हाइटफ्लाई", "सफेद मक्खी", "पांढरी माशी"],
    "aphid": ["aphid", "एफिड", "माहू", "तेला"],
    "thrips": ["thrips", "थ्रिप्स", "थ्रिप्स", "थ्रिप्स"],
    "mite": ["mite", "माइट", "मकड़ी", "रेड स्पाइडर माइट"],
    "pod_borer": ["pod borer", "पॉड बोरर", "फली छेदक", "इल्ली"],
    "fruit_borer": ["fruit borer", "फ्रूट बोरर", "फल छेदक"],
    "shoot_borer": ["shoot borer", "शूट बोरर", "शूट बोरर", "कांदा भेदक"],
}

CHEMICAL_KEYWORDS = [
    "chlorpyrifos", "thiamethoxam", "monocrotophos", "imidacloprid", "paraquat", "glyphosate",
    "triclopyr", "triclazole", "propiconazole", "chlorantraniliprole", "emamectin", "spinetoram",
    "fipronil", "haNPV", "npv", "carbendazim", "mancozeb", "copper oxychloride",
    "azoxystrobin", "tebuconazole", "hexaconazole", "difenoconazole", "flusilazole",
    "metribuzin", "pendimethalin", "quizalofop", "clodinafop", "sulfosulfuron",
    "urea", "dap", "mop", "ssp", "zinc sulphate", "ferrous sulphate",
    "borax", "boric acid", "blue vitriol", "neem oil", "neem cake",
]

DOSAGE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|gm|ग्राम|किग्रा|लीटर|मिली|मि\.ली\.)\s*(?:per|/|प्रति)\s*(ha|acre|हेक्टेयर|एकड़|liter|लीटर|plant|पौधा)',
    re.IGNORECASE
)

STATE_DISTRICT_MAP = {
    "andhra pradesh": ["visakhapatnam", "vijayawada", "guntur", "nellore", "kurnool", "anantapur"],
    "assam": ["guwahati", "dibrugarh", "silchar", "jorhat", "nagaon"],
    "bihar": ["patna", "gaya", "bhagalpur", "muzaffarpur", "darbhanga"],
    "chhattisgarh": ["raipur", "bilaspur", "durg", "korba", "raigarh"],
    "gujarat": ["ahmedabad", "surat", "vadodara", "rajkot", "bhavnagar", "jamnagar"],
    "haryana": ["gurugram", "faridabad", "panipat", "ambala", "hisar"],
    "himachal pradesh": ["shimla", "dharamshala", "solan", "mandi", "kullu"],
    "jharkhand": ["ranchi", "jamshedpur", "dhanbad", "bokaro", "hazaribagh"],
    "karnataka": ["bengaluru", "mysuru", "hubballi", "mangaluru", "belagavi"],
    "kerala": ["thiruvananthapuram", "kochi", "kozhikode", "thrissur", "kollam"],
    "madhya pradesh": ["bhopal", "indore", "gwalior", "jabalpur", "ujjain"],
    "maharashtra": ["mumbai", "pune", "nagpur", "nashik", "aurangabad", "solapur", "latur", "amravati", "kolhapur"],
    "odisha": ["bhubaneswar", "cuttack", "rourkela", "berhampur", "sambalpur"],
    "punjab": ["ludhiana", "amritsar", "jalandhar", "patiala", "bathinda"],
    "rajasthan": ["jaipur", "jodhpur", "kota", "bikaner", "udaipur"],
    "tamil nadu": ["chennai", "coimbatore", "madurai", "tiruchirappalli", "salem"],
    "telangana": ["hyderabad", "warangal", "nizamabad", "khammam", "karimnagar"],
    "uttar pradesh": ["lucknow", "kanpur", "ghaziabad", "agra", "varanasi", "meerut"],
    "uttarakhand": ["dehradun", "haridwar", "roorkee", "haldwani", "rishikesh"],
    "west bengal": ["kolkata", "howrah", "durgapur", "asansol", "siliguri"],
}

DOC_TYPE_KEYWORDS = {
    "advisory": ["advisory", "bulletin", "package of practices", "पैकेज", "सल्ला", "मार्गदर्शन", "recommendation", "advisory bulletin"],
    "textbook": ["textbook", "पाठ्यपुस्तक", "handbook", "हैंडबुक", "fundamentals", "principles", "introduction to"],
    "thesis": ["thesis", "dissertation", "शोध", "महाविद्यालय", "university", "submitted", "degree", "m.sc", "ph.d"],
    "extension": ["extension", "कृषि प्रसार", "farmer guide", "किसान गाइड", "कृषक मार्गदर्शिका", "folder", "पुस्तिका"],
}


# ============================================================
# Utility Functions
# ============================================================

def detect_language(text: str) -> str:
    """Detect language of text. Returns: en, mr, hi, gu, mixed"""
    if not text or len(text.strip()) < 20:
        return "unknown"
    try:
        lang = detect(text)
        lang_map = {"en": "en", "mr": "mr", "hi": "hi", "gu": "gu", "ta": "ta", "te": "te", "kn": "kn", "ml": "ml", "bn": "bn", "pa": "pa", "or": "or"}
        return lang_map.get(lang, "other")
    except LangDetectException:
        return "unknown"


def classify_doc_type(text: str, filename: str) -> str:
    """Classify document type from content and filename."""
    text_lower = (text + " " + filename).lower()
    scores = {}
    for dtype, keywords in DOC_TYPE_KEYWORDS.items():
        scores[dtype] = sum(1 for kw in keywords if kw in text_lower)
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "unknown"


def extract_entities(text: str) -> Dict[str, Any]:
    """Extract agronomic entities from text."""
    text_lower = text.lower()
    
    # Crops
    crops_found = []
    for crop, keywords in CROP_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            crops_found.append(crop)
    
    # Pests/Diseases
    pests_found = []
    for pest, keywords in PEST_DISEASE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            pests_found.append(pest)
    
    # Chemicals
    chemicals_found = []
    for chem in CHEMICAL_KEYWORDS:
        if chem in text_lower:
            chemicals_found.append(chem)
    
    # Dosages
    dosages = DOSAGE_PATTERN.findall(text)
    dosages_clean = [f"{amt} {unit}/{area}" for amt, unit, area in dosages]
    
    # Stage (days)
    stage_match = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*days?', text_lower)
    stage_min = int(stage_match.group(1)) if stage_match else 0
    stage_max = int(stage_match.group(2)) if stage_match else 120
    
    # Single day mention
    if stage_min == 0:
        single_day = re.search(r'(\d+)\s*days?\s*(?:old|stage|after)', text_lower)
        if single_day:
            stage_min = max(0, int(single_day.group(1)) - 10)
            stage_max = int(single_day.group(1)) + 10
    
    return {
        "crops": crops_found,
        "pests_diseases": pests_found,
        "chemicals": chemicals_found,
        "dosages": dosages_clean,
        "stage_min_days": stage_min,
        "stage_max_days": stage_max,
    }


def infer_location_from_path(filepath: str) -> tuple:
    """Infer state/district from folder path."""
    path_lower = filepath.lower()
    for state, districts in STATE_DISTRICT_MAP.items():
        if state in path_lower:
            for dist in districts:
                if dist in path_lower:
                    return dist.title(), state.title()
            # State found but no district
            return "", state.title()
    return "", ""


def estimate_authority_tier(doc_type: str, source_path: str) -> int:
    """Estimate authority tier (1=highest)."""
    path_lower = source_path.lower()
    if doc_type == "advisory":
        if any(kw in path_lower for kw in ["icar", "kisan", "kvk", "package of practices"]):
            return 1
        return 2
    elif doc_type == "extension":
        return 2
    elif doc_type == "textbook":
        return 3
    elif doc_type == "thesis":
        return 4
    return 3


def chunk_text(text: str, max_chunk_chars: int = 2000) -> List[str]:
    """Split text into chunks preserving recommendation boundaries."""
    # First split by double newline (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_chars:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def process_pdf(filepath: Path) -> List[PDFChunk]:
    """Process a single PDF file into chunks."""
    chunks = []
    filename = filepath.name
    rel_path = str(filepath)
    
    try:
        with pdfplumber.open(filepath) as pdf:
            all_pages_text = []
            page_languages = []
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                all_pages_text.append(page_text)
                if page_text.strip():
                    page_languages.append(detect_language(page_text))
            
            # Overall document classification
            full_text = "\n".join(all_pages_text)
            doc_type = classify_doc_type(full_text, filename)
            authority_tier = estimate_authority_tier(doc_type, rel_path)
            
            # Overall language
            lang_counts = {}
            for lang in page_languages:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"
            
            # Location inference
            district, state = infer_location_from_path(rel_path)
            
            # Entity extraction on full text
            entities = extract_entities(full_text)
            primary_crop = entities["crops"][0] if entities["crops"] else "General"
            
            # Chunk the text
            text_chunks = chunk_text(full_text)
            
            for j, chunk_str in enumerate(text_chunks):
                chunk_entities = extract_entities(chunk_str)
                
                chunk = PDFChunk(
                    chunk_id=f"{filepath.stem}_chunk_{j:04d}",
                    source_file=filename,
                    source_path=rel_path,
                    page_numbers=[],  # Could track which pages
                    doc_type=doc_type,
                    authority_tier=authority_tier,
                    language=primary_lang,
                    crop=chunk_entities["crops"][0] if chunk_entities["crops"] else primary_crop,
                    variety="",
                    stage_min_days=chunk_entities["stage_min_days"],
                    stage_max_days=chunk_entities["stage_max_days"],
                    district=district,
                    state=state,
                    season="Kharif",  # Default, could infer from content
                    valid_from="2024-01-01",
                    valid_until="2028-12-31",
                    text=chunk_str,
                    entities=chunk_entities,
                    extracted_at=datetime.now().isoformat()
                )
                chunks.append(chunk)
                
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Extract agricultural knowledge from PDFs")
    parser.add_argument("--input", required=True, help="Input folder path (recursive)")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--classify-only", action="store_true", help="Only classify PDFs, don't extract")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return
    
    # Find all PDFs
    pdf_files = list(input_path.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")
    
    if args.classify_only:
        for pdf_file in pdf_files[:20]:  # Sample first 20
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    sample_text = ""
                    for page in pdf.pages[:3]:
                        sample_text += page.extract_text() or ""
                    doc_type = classify_doc_type(sample_text, pdf_file.name)
                    lang = detect_language(sample_text[:1000])
                    print(f"  {pdf_file.relative_to(input_path)} -> type={doc_type}, lang={lang}")
            except Exception as e:
                print(f"  {pdf_file.relative_to(input_path)} -> ERROR: {e}")
        return
    
    # Process all PDFs
    all_chunks = []
    for i, pdf_file in enumerate(pdf_files):
        print(f"[{i+1}/{len(pdf_files)}] Processing: {pdf_file.name}")
        file_chunks = process_pdf(pdf_file)
        all_chunks.extend(file_chunks)
        print(f"  -> {len(file_chunks)} chunks extracted")
    
    # Write JSONL
    with open(args.output, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
    
    print(f"\nDone! {len(all_chunks)} total chunks written to {args.output}")
    
    # Print summary
    crops = {}
    langs = {}
    types = {}
    for chunk in all_chunks:
        crops[chunk.crop] = crops.get(chunk.crop, 0) + 1
        langs[chunk.language] = langs.get(chunk.language, 0) + 1
        types[chunk.doc_type] = types.get(chunk.doc_type, 0) + 1
    
    print("\nSummary:")
    print(f"  Crops: {dict(sorted(crops.items(), key=lambda x: -x[1]))}")
    print(f"  Languages: {langs}")
    print(f"  Doc Types: {types}")


if __name__ == "__main__":
    main()