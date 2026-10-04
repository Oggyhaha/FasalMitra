#!/usr/bin/env python3
"""
Fast Parallel Ingestion - Fixed for Windows
"""

import os
import json
import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

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

DOMAINS = {
    "crops": {"keywords": ["crop", "पिक", "फसल", "kheti", "खेती"], "subtypes": ["cereals", "pulses", "oilseeds", "commercial", "fodder", "vegetables"]},
    "livestock": {"keywords": ["livestock", "पशु", "मवेशी", "पशुपालन", "dairy", "दुग्ध", "cattle", "भैंस", "बकरी", "पोल्ट्री", "मुर्गी", "fisheries", "मछली"], "subtypes": ["dairy", "poultry", "goat", "sheep", "fisheries", "piggery"]},
    "fruits": {"keywords": ["fruit", "फल", "horticulture", "बागवानी", "mango", "आम", "केला", "banana", "पपीता", "papaya", "अनार", "guava", "संतरा", "नींबू", "coconut"], "subtypes": ["tropical", "subtropical", "temperate", "plantation", "nuts"]},
    "vegetables": {"keywords": ["vegetable", "सब्जी", "भाजी", "tomato", "प्याज", "आलू", "मिर्च", "बैंगन", "भिंडी", "okra"], "subtypes": ["solanaceous", "cucurbit", "root", "leafy", "legume"]},
    "weather": {"keywords": ["weather", "मौसम", "हवामान", "rainfall", "वर्षा", "temperature", "humidity", "forecast", "agromet"], "subtypes": ["forecast", "historical", "advisory", "extreme"]},
    "market": {"keywords": ["market", "मंडी", "बाजार", "price", "भाव", "कीमत", "rate", "arrival", "mandi", "MSP"], "subtypes": ["price", "arrival", "trend", "procurement"]},
    "schemes": {"keywords": ["scheme", "योजना", "subsidy", "सब्सिडी", "loan", "ऋण", "insurance", "बीमा", "PM-KISAN"], "subtypes": ["central", "state", "insurance", "credit", "subsidy"]},
    "soil_water": {"keywords": ["soil", "मिट्टी", "water", "पानी", "irrigation", "सिंचाई", "fertilizer", "उर्वरक", "organic", "जैविक"], "subtypes": ["soil_health", "irrigation", "fertilizer", "organic"]},
}

@dataclass
class KnowledgeChunk:
    chunk_id: str
    source_file: str
    source_path: str
    file_type: str
    domain: str
    subdomain: str
    doc_type: str
    authority_tier: int
    language: str
    title: str
    content: str
    metadata: Dict[str, Any]
    entities: Dict[str, Any]
    extracted_at: str


def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 20: return "unknown"
    try:
        lang = detect(text)
        lang_map = {"en": "en", "mr": "mr", "hi": "hi", "gu": "gu", "ta": "ta", "te": "te", "kn": "kn", "ml": "ml", "bn": "bn", "pa": "pa", "or": "or"}
        return lang_map.get(lang, "other")
    except LangDetectException: return "unknown"


def classify_domain(text: str, filepath: str) -> tuple:
    text_lower = (text + " " + str(filepath)).lower()
    domain_scores = {}
    for domain, config in DOMAINS.items():
        domain_scores[domain] = sum(1 for kw in config["keywords"] if kw in text_lower)
    primary_domain = max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else "general"
    subdomain = ""
    if primary_domain in DOMAINS:
        for sub in DOMAINS[primary_domain]["subtypes"]:
            if sub in text_lower: subdomain = sub; break
    return primary_domain, subdomain


def classify_doc_type(text: str, filepath: str, file_type: str) -> str:
    text_lower = (text + " " + str(filepath)).lower()
    if file_type in ("csv", "xlsx"): return "dataset"
    if file_type == "json": return "api_data"
    type_keywords = {
        "advisory": ["advisory", "bulletin", "package of practices", "recommendation", "सल्ला", "मार्गदर्शन", "पैकेज"],
        "textbook": ["textbook", "पाठ्यपुस्तक", "handbook", "fundamentals", "principles"],
        "thesis": ["thesis", "dissertation", "शोध", "m.sc", "ph.d"],
        "extension": ["extension", "कृषि प्रसार", "farmer guide", "किसान गाइड", "folder", "पुस्तिका"],
        "scheme_doc": ["scheme", "योजना", "guidelines", "दिशानिर्देश"],
        "report": ["report", "रिपोर्ट", "survey", "सर्वेक्षण", "census"],
        "training": ["training", "प्रशिक्षण", "module", "capacity building"],
    }
    for dtype, keywords in type_keywords.items():
        if any(kw in text_lower for kw in keywords): return dtype
    return "document"


def extract_entities(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    entities = {"crops": [], "livestock": [], "chemicals": [], "dosages": [], "numbers": []}
    crop_keywords = ["rice", "wheat", "maize", "cotton", "soybean", "sugarcane", "chickpea", "pigeonpea", "groundnut", "mustard", "mango", "banana", "citrus", "pomegranate", "guava", "coconut", "tomato", "onion", "potato", "chilli", "brinjal", "okra"]
    for c in crop_keywords:
        if c in text_lower: entities["crops"].append(c)
    livestock_keywords = ["cattle", "buffalo", "goat", "sheep", "poultry", "भैंस", "बकरी", "मुर्गी", "मछली"]
    for l in livestock_keywords:
        if l in text_lower: entities["livestock"].append(l)
    chem_keywords = ["urea", "dap", "mop", "ssp", "zinc", "boron", "gypsum", "neem", "chlorpyrifos", "imidacloprid", "thiamethoxam", "carbendazim", "mancozeb", "propiconazole"]
    for c in chem_keywords:
        if c in text_lower: entities["chemicals"].append(c)
    dosage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|gm|ग्राम|किग्रा|लीटर|मिली)\s*(?:per|/|प्रति)\s*(ha|acre|हेक्टेयर|एकड़|liter|लीटर|plant|पौधा|kg)', re.IGNORECASE)
    entities["dosages"] = [f"{amt} {unit}/{area}" for amt, unit, area in dosage_pattern.findall(text)]
    entities["numbers"] = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:rs|₹|/kg|/quintal|/ha|/acre|%|percent)\b', text_lower)
    return entities


def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
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


def check_pdf_has_text(filepath: Path) -> tuple:
    try:
        with pdfplumber.open(filepath) as pdf:
            page_count = len(pdf.pages)
            sample_text = ""
            for i, page in enumerate(pdf.pages[:3]):
                t = page.extract_text() or ""
                sample_text += t
            has_text = len(sample_text.strip()) > 100
            return has_text, sample_text[:2000], page_count
    except Exception:
        return False, "", 0


def process_pdf_file(filepath: Path) -> List[KnowledgeChunk]:
    has_text, sample_text, page_count = check_pdf_has_text(filepath)
    if not has_text:
        return []
    
    try:
        with pdfplumber.open(filepath) as pdf:
            all_text = []
            page_langs = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                all_text.append(page_text)
                if page_text.strip():
                    page_langs.append(detect_language(page_text))
        
        full_text = "\n".join(all_text)
        if not full_text.strip(): return []
        
        domain, subdomain = classify_domain(full_text, str(filepath))
        doc_type = classify_doc_type(full_text, str(filepath), "pdf")
        authority = 1 if any(k in str(filepath).lower() for k in ["icar", "kvk", "kisan"]) else (2 if doc_type in ["advisory", "extension"] else 3)
        
        lang_counts = {}
        for lang in page_langs:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"
        
        entities = extract_entities(full_text)
        text_chunks = chunk_text(full_text)
        chunks = []
        
        for j, chunk_str in enumerate(text_chunks):
            chunk_entities = extract_entities(chunk_str)
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_chunk_{j:04d}",
                source_file=filepath.name, source_path=str(filepath),
                file_type="pdf", domain=domain, subdomain=subdomain,
                doc_type=doc_type, authority_tier=authority, language=primary_lang,
                title=f"{chunk_entities.get('crops', [''])[0] or domain} - {filepath.name}",
                content=chunk_str,
                metadata={"pages": page_count, "chunk_index": j},
                entities=chunk_entities,
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
        return chunks
    except Exception as e:
        print(f"  Error: {e}")
        return []


def process_csv(filepath: Path) -> List[KnowledgeChunk]:
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
                source_file=filepath.name, source_path=str(filepath),
                file_type=filepath.suffix[1:], domain="", subdomain="",
                doc_type="dataset", authority_tier=2, language="en",
                title=f"{filepath.stem} (rows {start+1}-{end})",
                content=summary,
                metadata={"columns": df.columns.tolist(), "total_rows": total_rows, "row_range": f"{start+1}-{end}"},
                entities=extract_entities(summary),
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  CSV/Excel error: {e}")
    return chunks


def process_json(filepath: Path) -> List[KnowledgeChunk]:
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [{"data": data}])
        for i, item in enumerate(items[:100]):
            content = json.dumps(item, ensure_ascii=False, indent=2)[:3000]
            entities = extract_entities(content)
            domain, subdomain = classify_domain(content, str(filepath))
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_item_{i:04d}",
                source_file=filepath.name, source_path=str(filepath),
                file_type="json", domain=domain, subdomain=subdomain,
                doc_type="api_data", authority_tier=3, language=detect_language(content),
                title=f"{filepath.stem} item {i}", content=content,
                metadata={"item_index": i, "total_items": len(items)},
                entities=entities, extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  JSON error: {e}")
    return chunks


def process_text(filepath: Path) -> List[KnowledgeChunk]:
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip(): return chunks
        domain, subdomain = classify_domain(text, str(filepath))
        doc_type = classify_doc_type(text, str(filepath), "txt")
        entities = extract_entities(text)
        text_chunks = chunk_text(text)
        for j, chunk_str in enumerate(text_chunks):
            chunk = KnowledgeChunk(
                chunk_id=f"{filepath.stem}_chunk_{j:04d}",
                source_file=filepath.name, source_path=str(filepath),
                file_type="txt", domain=domain, subdomain=subdomain,
                doc_type=doc_type, authority_tier=3, language=detect_language(text),
                title=f"{filepath.stem} - part {j+1}", content=chunk_str,
                metadata={"chunk_index": j}, entities=extract_entities(chunk_str),
                extracted_at=datetime.now().isoformat()
            )
            chunks.append(chunk)
    except Exception as e:
        print(f"  Text error: {e}")
    return chunks


def worker_process_file(filepath_str: str, input_root_str: str) -> tuple:
    """Worker function for parallel processing - must be at module level for pickling."""
    filepath = Path(filepath_str)
    input_root = Path(input_root_str)
    
    try:
        if filepath.suffix.lower() == ".pdf":
            has_text, _, _ = check_pdf_has_text(filepath)
            if not has_text:
                return (filepath_str, [], "SKIPPED: scanned/image PDF")
            chunks = process_pdf_file(filepath)
        elif filepath.suffix.lower() in (".csv", ".xlsx", ".xls"):
            chunks = process_csv(filepath)
        elif filepath.suffix.lower() == ".json":
            chunks = process_json(filepath)
        elif filepath.suffix.lower() in (".txt", ".md"):
            chunks = process_text(filepath)
        else:
            return (filepath_str, [], f"SKIPPED: unsupported {filepath.suffix}")
        
        for chunk in chunks:
            if not chunk.domain:
                chunk.domain, chunk.subdomain = classify_domain(chunk.content, str(filepath))
        return (filepath_str, chunks, None)
    except Exception as e:
        return (filepath_str, [], f"ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Fast parallel ingestion")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ext", nargs="+", default=[".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt", ".md"])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-files", type=int)
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return
    
    all_files = []
    for ext in args.ext:
        all_files.extend(input_path.rglob(f"*{ext}"))
    
    if args.max_files:
        all_files = all_files[:args.max_files]
    
    print(f"Found {len(all_files)} files. Processing with {args.workers} workers...")
    
    # Convert to strings for pickling
    file_strings = [str(f) for f in all_files]
    input_root_str = str(input_path)
    
    all_chunks = []
    processed = 0
    
    # Use spawn context for Windows
    ctx = multiprocessing.get_context("spawn")
    
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as executor:
        futures = {executor.submit(worker_process_file, f, input_root_str): f for f in file_strings}
        
        for future in as_completed(futures):
            filepath_str = futures[future]
            processed += 1
            try:
                fp_str, chunks, error = future.result()
                filepath = Path(fp_str)
                if error and not error.startswith("SKIPPED"):
                    print(f"[{processed}/{len(all_files)}] {filepath.relative_to(input_path)} - {error}")
                elif error:
                    print(f"[{processed}/{len(all_files)}] {filepath.relative_to(input_path)} - {error}")
                else:
                    print(f"[{processed}/{len(all_files)}] {filepath.relative_to(input_path)} - OK {len(chunks)} chunks")
                    for chunk in chunks:
                        if not chunk.domain:
                            chunk.domain, chunk.subdomain = classify_domain(chunk.content, fp_str)
                        all_chunks.append(chunk)
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
    print(f"Domains: {domains}")
    print(f"Doc Types: {types}")
    print(f"Languages: {langs}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()