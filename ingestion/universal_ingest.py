#!/usr/bin/env python3
"""
Universal Ingestion Pipeline for FasalMitra
Handles: PDF, CSV, Excel, JSON, Text
Domains: Crops, Livestock, Fruits, Fisheries, Weather, Market, Schemes
"""

import os
import json
import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, asdict
from datetime import datetime
import signal

try:
    import pdfplumber
except ImportError:
    os.system("pip install pdfplumber -q")
    import pdfplumber

try:
    import pandas as pd
except ImportError:
    os.system("pip install pandas openpyxl -q")
    import pandas as pd

try:
    from langdetect import detect, LangDetectException
except ImportError:
    os.system("pip install langdetect -q")
    from langdetect import detect, LangDetectException

sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# Domain Configuration
# ============================================================

DOMAINS = {
    "crops": {
        "keywords": ["crop", "पिक", "फसल", "పంట", "ಫಸಲು", "व्यवसाय", "kheti", "खेती"],
        "subtypes": ["cereals", "pulses", "oilseeds", "commercial", "fodder", "vegetables"],
    },
    "livestock": {
        "keywords": ["livestock", "पशु", "मवेशी", "पशुपालन", "dairy", "दुग्ध", "गोपालन", 
                     "cattle", "भैंस", "बकरी", "भेड़", "कुक्कुट", "पोल्ट्री", "मुर्गी",
                     "fisheries", "मछली", "मत्स्य", "aquaculture"],
        "subtypes": ["dairy", "poultry", "goat", "sheep", "fisheries", "piggery"],
    },
    "fruits": {
        "keywords": ["fruit", "फल", "फळ", "पैठणी", "horticulture", "बागवानी", "उद्यानिकी",
                     "mango", "आम", "केला", "banana", "पपीता", "papaya", "अनार", "pomegranate",
                     "guava", "अमरूद", "संतरा", "orange", "नींबू", "lemon", "लीची", "litchi",
                     "coconut", "नारियल", "सुपारी", "arecanut"],
        "subtypes": ["tropical", "subtropical", "temperate", "plantation", "nuts"],
    },
    "vegetables": {
        "keywords": ["vegetable", "सब्जी", "भाजी", "शाक", "टमाटर", "tomato", "प्याज", "onion",
                     "आलू", "potato", "मिर्च", "chilli", "बैंगन", "brinjal", "भिंडी", "okra",
                     "कद्दू", "pumpkin", "लौकी", "bottle gourd", "करेला", "bitter gourd"],
        "subtypes": ["solanaceous", "cucurbit", "root", "leafy", "legume"],
    },
    "weather": {
        "keywords": ["weather", "मौसम", "हवामान", "rainfall", "वर्षा", "बारिश", "temperature", "तापमान",
                     "humidity", "आर्द्रता", "forecast", "पूर्वानुमान", "agromet", "कृषि मौसम"],
        "subtypes": ["forecast", "historical", "advisory", "extreme"],
    },
    "market": {
        "keywords": ["market", "मंडी", "बाजार", "price", "भाव", "कीमत", "rate", "दर",
                     "arrival", "आवक", "mandi", "procurement", "खरीद", "MSP", "न्यूनतम समर्थन मूल्य"],
        "subtypes": ["price", "arrival", "trend", "procurement"],
    },
    "schemes": {
        "keywords": ["scheme", "योजना", "स्कीम", "subsidy", "सब्सिडी", "अनुदान", "loan", "ऋण",
                     "insurance", "बीमा", "कृषि बीमा", "PM-KISAN", "किसान सम्मान", "किसान क्रेडिट"],
        "subtypes": ["central", "state", "insurance", "credit", "subsidy"],
    },
    "soil_water": {
        "keywords": ["soil", "मिट्टी", "माती", "water", "पानी", "पाणी", "irrigation", "सिंचाई",
                     "fertilizer", "उर्वरक", "खाद", "nutrient", "पोषक", "organic", "जैविक"],
        "subtypes": ["soil_health", "irrigation", "fertilizer", "organic", "watershed"],
    },
}

# ============================================================
# Data Classes
# ============================================================

@dataclass
class KnowledgeChunk:
    chunk_id: str
    source_file: str
    source_path: str
    file_type: str  # pdf, csv, xlsx, json, txt
    domain: str     # crops, livestock, fruits, etc.
    subdomain: str
    doc_type: str   # advisory, textbook, dataset, report, scheme, etc.
    authority_tier: int
    language: str
    title: str
    content: str
    metadata: Dict[str, Any]
    entities: Dict[str, Any]
    extracted_at: str


# ============================================================
# Utility Functions
# ============================================================

def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 20:
        return "unknown"
    try:
        lang = detect(text)
        lang_map = {"en": "en", "mr": "mr", "hi": "hi", "gu": "gu", "ta": "ta", 
                    "te": "te", "kn": "kn", "ml": "ml", "bn": "bn", "pa": "pa", "or": "or"}
        return lang_map.get(lang, "other")
    except LangDetectException:
        return "unknown"


def classify_domain(text: str, filepath: str) -> tuple:
    """Classify domain and subdomain from content and path."""
    text_lower = (text + " " + str(filepath)).lower()
    
    domain_scores = {}
    for domain, config in DOMAINS.items():
        score = sum(1 for kw in config["keywords"] if kw in text_lower)
        domain_scores[domain] = score
    
    primary_domain = max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else "general"
    
    # Subdomain
    subdomain = ""
    if primary_domain in DOMAINS:
        for sub in DOMAINS[primary_domain]["subtypes"]:
            if sub in text_lower:
                subdomain = sub
                break
    
    return primary_domain, subdomain


def classify_doc_type(text: str, filepath: str, file_type: str) -> str:
    """Classify document type."""
    text_lower = (text + " " + str(filepath)).lower()
    
    if file_type == "csv" or file_type == "xlsx":
        return "dataset"
    if file_type == "json":
        return "api_data"
    
    type_keywords = {
        "advisory": ["advisory", "bulletin", "package of practices", "recommendation", "सल्ला", "मार्गदर्शन", "पैकेज"],
        "textbook": ["textbook", "पाठ्यपुस्तक", "handbook", "fundamentals", "principles"],
        "thesis": ["thesis", "dissertation", "शोध", "m.sc", "ph.d", "submitted"],
        "extension": ["extension", "कृषि प्रसार", "farmer guide", "किसान गाइड", "folder", "पुस्तिका"],
        "scheme_doc": ["scheme", "योजना", "guidelines", "दिशानिर्देश", "operational guidelines"],
        "report": ["report", "रिपोर्ट", "survey", "सर्वेक्षण", "census", "गणना"],
        "training": ["training", "प्रशिक्षण", "module", "मॉड्यूल", "capacity building"],
    }
    
    for dtype, keywords in type_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return dtype
    return "document"


def extract_entities(text: str) -> Dict[str, Any]:
    """Extract domain-agnostic entities."""
    text_lower = text.lower()
    
    entities = {
        "crops": [],
        "livestock": [],
        "varieties": [],
        "diseases_pests": [],
        "chemicals": [],
        "fertilizers": [],
        "dosages": [],
        "stages": [],
        "locations": [],
        "numbers": [],
    }
    
    # Crops (broad)
    crop_keywords = ["rice", "wheat", "maize", "cotton", "soybean", "sugarcane", "chickpea", "pigeonpea",
                     "groundnut", "mustard", "sesame", "sunflower", "sorghum", "millet", "barley",
                     "mango", "banana", "citrus", "pomegranate", "guava", "papaya", "coconut", "cashew",
                     "tomato", "onion", "potato", "chilli", "brinjal", "okra", "cabbage", "cauliflower"]
    for c in crop_keywords:
        if c in text_lower:
            entities["crops"].append(c)
    
    # Livestock
    livestock_keywords = ["cattle", "buffalo", "goat", "sheep", "poultry", "cow", "भैंस", "बकरी", "मुर्गी", "मछली"]
    for l in livestock_keywords:
        if l in text_lower:
            entities["livestock"].append(l)
    
    # Chemicals/fertilizers
    chem_keywords = ["urea", "dap", "mop", "ssp", "zinc", "boron", "gypsum", "neem", "chlorpyrifos",
                     "imidacloprid", "thiamethoxam", "carbendazim", "mancozeb", "propiconazole"]
    for c in chem_keywords:
        if c in text_lower:
            entities["chemicals"].append(c)
    
    # Dosages
    dosage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|gm|ग्राम|किग्रा|लीटर|मिली)\s*(?:per|/|प्रति)\s*(ha|acre|हेक्टेयर|एकड़|liter|लीटर|plant|पौधा|kg)', re.IGNORECASE)
    entities["dosages"] = [f"{amt} {unit}/{area}" for amt, unit, area in dosage_pattern.findall(text)]
    
    # Numbers (prices, rates, quantities)
    entities["numbers"] = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:rs|₹|/kg|/quintal|/ha|/acre|%|percent)\b', text_lower)
    
    return entities


def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """Smart chunking by paragraphs."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += ("\n\n" if current else "") + para
        else:
            if current: chunks.append(current)
            current = para
    if current: chunks.append(current)
    return chunks


def process_csv(filepath: Path) -> List[KnowledgeChunk]:
    """Process CSV/Excel files as structured datasets."""
    chunks = []
    try:
        if filepath.suffix.lower() == ".csv":
            df = pd.read_csv(filepath, encoding_errors="ignore", low_memory=False)
        else:
            df = pd.read_excel(filepath)
        
        rows_per_chunk = 50
        total_rows = len(df)
        
        for start in range(0, total_rows, rows_per_chunk):
            end = min(start + rows_per_chunk, total_rows)
            chunk_df = df.iloc[start:end]
            
            content = chunk_df.to_string(index=False)
            
            summary = f"Dataset: {filepath.stem}\nColumns: {', '.join(df.columns.tolist())}\nRows: {total_rows}\nSample:\n{content[:2000]}"
            
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_rows_{start}_{end}",
                source_file=filepath.name,
                source_path=str(filepath),
                file_type=filepath.suffix[1:],
                domain="",
                subdomain="",
                doc_type="dataset",
                authority_tier=2,
                language="en",
                title=f"{filepath.stem} (rows {start+1}-{end})",
                content=summary,
                metadata={
                    "columns": df.columns.tolist(),
                    "total_rows": total_rows,
                    "row_range": f"{start+1}-{end}",
                },
                entities=extract_entities(summary),
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  CSV/Excel error: {e}")
    return chunks


def process_pdf(filepath: Path, timeout_sec: int = 60) -> List[KnowledgeChunk]:
    """Process PDF with timeout."""
    chunks = []
    filename = filepath.name
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"PDF processing timeout ({timeout_sec}s)")
    
    try:
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_sec)
        
        with pdfplumber.open(filepath) as pdf:
            all_text = []
            page_langs = []
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                all_text.append(page_text)
                if page_text.strip():
                    page_langs.append(detect_language(page_text))
            
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            full_text = "\n".join(all_text)
            if not full_text.strip():
                return chunks
            
            domain, subdomain = classify_domain(full_text, str(filepath))
            doc_type = classify_doc_type(full_text, str(filepath), "pdf")
            authority = 1 if any(k in str(filepath).lower() for k in ["icar", "kvk", "kisan"]) else (2 if doc_type in ["advisory", "extension"] else 3)
            
            lang_counts = {}
            for lang in page_langs:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"
            
            entities = extract_entities(full_text)
            
            text_chunks = chunk_text(full_text)
            
            for j, chunk_str in enumerate(text_chunks):
                chunk_entities = extract_entities(chunk_str)
                
                chunk = KnowledgeChunk(
                    chunk_id=f"{filepath.stem}_chunk_{j:04d}",
                    source_file=filename,
                    source_path=str(filepath),
                    file_type="pdf",
                    domain=domain,
                    subdomain=subdomain,
                    doc_type=doc_type,
                    authority_tier=authority,
                    language=primary_lang,
                    title=f"{chunk_entities.get('crops', [''])[0] or domain} - {filename}",
                    content=chunk_str,
                    metadata={"pages": len(pdf.pages), "chunk_index": j},
                    entities=chunk_entities,
                    extracted_at=datetime.now().isoformat()
                )
                chunks.append(chunk)
                
    except TimeoutError:
        print(f"  Timeout after {timeout_sec}s - skipping")
    except Exception as e:
        print(f"  Error: {e}")
    
    return chunks


def process_json(filepath: Path) -> List[KnowledgeChunk]:
    """Process JSON files."""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = [data]
        else:
            items = [{"data": data}]
        
        for i, item in enumerate(items[:100]):
            content = json.dumps(item, ensure_ascii=False, indent=2)[:3000]
            entities = extract_entities(content)
            domain, subdomain = classify_domain(content, str(filepath))
            
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_item_{i:04d}",
                source_file=filepath.name,
                source_path=str(filepath),
                file_type="json",
                domain=domain,
                subdomain=subdomain,
                doc_type="api_data",
                authority_tier=3,
                language=detect_language(content),
                title=f"{filepath.stem} item {i}",
                content=content,
                metadata={"item_index": i, "total_items": len(items)},
                entities=entities,
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  JSON error: {e}")
    return chunks


def process_text(filepath: Path) -> List[KnowledgeChunk]:
    """Process plain text files."""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        if not text.strip():
            return chunks
        
        domain, subdomain = classify_domain(text, str(filepath))
        doc_type = classify_doc_type(text, str(filepath), "txt")
        entities = extract_entities(text)
        
        text_chunks = chunk_text(text)
        for j, chunk_str in enumerate(text_chunks):
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_chunk_{j:04d}",
                source_file=filepath.name,
                source_path=str(filepath),
                file_type="txt",
                domain=domain,
                subdomain=subdomain,
                doc_type=doc_type,
                authority_tier=3,
                language=detect_language(text),
                title=f"{filepath.stem} - part {j+1}",
                content=chunk_str,
                metadata={"chunk_index": j},
                entities=extract_entities(chunk_str),
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  Text error: {e}")
    return chunks


# ============================================================
# Main Processor
# ============================================================

FILE_PROCESSORS = {
    ".pdf": process_pdf,
    ".csv": process_csv,
    ".xlsx": process_csv,
    ".xls": process_csv,
    ".json": process_json,
    ".txt": process_text,
    ".md": process_text,
}


def main():
    parser = argparse.ArgumentParser(description="Universal knowledge ingestion for FasalMitra")
    parser.add_argument("--input", required=True, help="Input folder (recursive)")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--ext", nargs="+", default=list(FILE_PROCESSORS.keys()), 
                       help="File extensions to process")
    parser.add_argument("--timeout", type=int, default=60, help="PDF timeout seconds")
    parser.add_argument("--max-files", type=int, help="Limit files for testing")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        return
    
    all_files = []
    for ext in args.ext:
        all_files.extend(input_path.rglob(f"*{ext}"))
    
    if args.max_files:
        all_files = all_files[:args.max_files]
    
    print(f"Found {len(all_files)} files to process")
    
    all_chunks = []
    for i, filepath in enumerate(all_files):
        print(f"[{i+1}/{len(all_files)}] {filepath.relative_to(input_path)} ({filepath.suffix})")
        
        processor = FILE_PROCESSORS.get(filepath.suffix.lower())
        if not processor:
            print(f"  SKIP: Unsupported {filepath.suffix}")
            continue
        
        try:
            if filepath.suffix.lower() == ".pdf":
                file_chunks = processor(filepath, timeout_sec=args.timeout)
            else:
                file_chunks = processor(filepath)
            
            for chunk in file_chunks:
                if not chunk.domain:
                    chunk.domain, chunk.subdomain = classify_domain(chunk.content, str(filepath))
                all_chunks.append(chunk)
            
            print(f"  OK {len(file_chunks)} chunks")
        except Exception as e:
            print(f"  FAILED: {e}")
    
    with open(args.output, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
    
    print(f"\nDone! {len(all_chunks)} chunks -> {args.output}")
    
    domains = {}
    types = {}
    langs = {}
    for c in all_chunks:
        domains[c.domain] = domains.get(c.domain, 0) + 1
        types[c.doc_type] = types.get(c.doc_type, 0) + 1
        langs[c.language] = langs.get(c.language, 0) + 1
    
    print(f"\nDomains: {domains}")
    print(f"Doc Types: {types}")
    print(f"Languages: {langs}")


if __name__ == "__main__":
    main()