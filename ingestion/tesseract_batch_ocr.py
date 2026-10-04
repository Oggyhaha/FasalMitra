#!/usr/bin/env python3
"""
Batch OCR with Tesseract for Scanned Agricultural PDFs
Supports Hindi, English, Marathi
"""

import os
import json
import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import fitz  # pymupdf
except ImportError:
    os.system("pip install pymupdf -q")
    import fitz

try:
    import pytesseract
except ImportError:
    os.system("pip install pytesseract -q")
    import pytesseract

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
    """Simple language detection based on script."""
    if not text or len(text.strip()) < 20:
        return "unknown"
    
    # Check for Devanagari (Hindi/Marathi)
    devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    # Check for Latin
    latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    
    if devanagari_chars > latin_chars:
        return "hi"  # Could be Hindi or Marathi
    return "en"


def classify_domain(text: str, filepath: str) -> tuple:
    text_lower = (text + " " + str(filepath)).lower()
    
    domain_keywords = {
        "livestock": ["livestock", "पशु", "मवेशी", "पशुपालन", "dairy", "दुग्ध", "gopalan", "cattle", "भैंस", "बकरी", "पोल्ट्री", "मुर्गी", "fisheries", "मछली"],
        "fruits": ["fruit", "फल", "horticulture", "बागवानी", "mango", "आम", "केला", "banana", "पपीता", "guava", "अमरूद", "संतरा", "नींबू", "coconut", "नारियल"],
        "vegetables": ["vegetable", "सब्जी", "भाजी", "tomato", "प्याज", "onion", "आलू", "potato", "मिर्च", "chilli", "बैंगन", "भिंडी", "okra"],
        "weather": ["weather", "मौसम", "हवामान", "rainfall", "वर्षा", "बारिश", "temperature", "humidity", "forecast", "पूर्वानुमान", "agromet"],
        "market": ["market", "मंडी", "बाजार", "price", "भाव", "कीमत", "rate", "arrival", "mandi", "procurement", "MSP"],
        "schemes": ["scheme", "योजना", "subsidy", "सब्सिडी", "loan", "ऋण", "insurance", "बीमा", "PM-KISAN", "किसान सम्मान"],
        "soil_water": ["soil", "मिट्टी", "water", "पानी", "irrigation", "सिंचाई", "fertilizer", "उर्वरक", "खाद", "organic", "जैविक"],
        "crops": ["crop", "पिक", "फसल", "kheti", "खेती", "cultivation", "sowing", "बुआई", "harvest", "कटाई", "yield", "उत्पादन", "variety", "किस्म", "seed", "बीज"],
    }
    
    scores = {}
    for domain, keywords in domain_keywords.items():
        scores[domain] = sum(2 if kw in text_lower else 0 for kw in keywords)
    
    primary_domain = max(scores, key=scores.get) if max(scores.values()) > 0 else "crops"
    
    subdomain = ""
    if primary_domain == "crops":
        if any(k in text_lower for k in ["wheat", "गेहूं", "rice", "धान", "paddy"]): subdomain = "cereals"
        elif any(k in text_lower for k in ["cotton", "कपास"]): subdomain = "fiber"
        elif any(k in text_lower for k in ["soybean", "सोयाबीन", "groundnut"]): subdomain = "oilseeds"
    elif primary_domain == "livestock":
        if any(k in text_lower for k in ["dairy", "milk", "दूध"]): subdomain = "dairy"
        elif any(k in text_lower for k in ["poultry", "मुर्गी"]): subdomain = "poultry"
    
    return primary_domain, subdomain


def extract_entities(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    entities = {"crops": [], "livestock": [], "chemicals": [], "dosages": [], "numbers": []}
    crop_keywords = ["wheat", "गेहूं", "rice", "धान", "cotton", "कपास", "soybean", "सोयाबीन", "maize", "मक्का", "chickpea", "चना", "mango", "आम", "banana", "केला"]
    for c in crop_keywords:
        if c in text_lower: entities["crops"].append(c)
    livestock_keywords = ["cattle", "buffalo", "goat", "भैंस", "बकरी", "पोल्ट्री", "मुर्गी", "dairy", "दूध"]
    for l in livestock_keywords:
        if l in text_lower: entities["livestock"].append(l)
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


def is_scanned_pdf(pdf_path: Path) -> bool:
    """Quick check if PDF has extractable text."""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc[:3]:
                text = page.get_text()
                if text and len(text.strip()) > 100:
                    return False
        return True
    except:
        return True


def process_pdf_ocr(pdf_path: Path, output_dir: Path) -> Dict:
    """OCR a single PDF with Tesseract (Hindi + English)."""
    print(f"  OCR: {pdf_path.name}")
    
    try:
        doc = fitz.open(pdf_path)
        all_text = []
        
        for page_num, page in enumerate(doc):
            # Render at 300 DPI for good OCR
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("ppm")
            
            with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            
            try:
                # Try Hindi first (for Devanagari), then English
                text = pytesseract.image_to_string(tmp_path, lang='hin+eng', config='--psm 6 --oem 3')
                
                if text and len(text.strip()) > 50:
                    all_text.append(f"--- Page {page_num+1} ---\n{text}")
            finally:
                os.unlink(tmp_path)
        
        doc.close()
        
        full_text = "\n\n".join(all_text)
        if not full_text.strip():
            return {"success": False, "error": "No text extracted"}
        
        # Save OCR text
        output_dir.mkdir(parents=True, exist_ok=True)
        txt_file = output_dir / f"{pdf_path.stem}_ocr.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        return {"success": True, "pages": len(doc), "text": full_text, "chars": len(full_text)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_file(pdf_path: Path, output_dir: Path) -> tuple:
    """Worker function for parallel processing."""
    filepath_str = str(pdf_path)
    try:
        if not is_scanned_pdf(pdf_path):
            return (filepath_str, [], "SKIPPED: Already has text")
        
        result = process_pdf_ocr(pdf_path, output_dir)
        if result['success']:
            return (filepath_str, result, None)
        return (filepath_str, [], f"FAILED: {result.get('error')}")
    except Exception as e:
        return (filepath_str, [], f"ERROR: {e}")


def batch_ocr(input_dir: Path, output_dir: Path, max_workers: int = 2):
    """Process all PDFs in parallel."""
    pdf_files = list(input_dir.rglob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")
    
    # Filter scanned PDFs
    scanned = [f for f in pdf_files if is_scanned_pdf(f)]
    print(f"Scanned PDFs to OCR: {len(scanned)}")
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f, output_dir): f for f in scanned}
        
        for future in as_completed(futures):
            pdf = futures[future]
            try:
                fp, result, error = future.result()
                filepath = Path(fp)
                if error and not error.startswith("SKIPPED"):
                    print(f"  FAIL {filepath.relative_to(input_dir)}: {error}")
                elif error:
                    print(f"  SKIP {filepath.relative_to(input_dir)}: {error}")
                else:
                    print(f"  OK {filepath.relative_to(input_dir)}: {result['pages']} pages, {result['chars']} chars")
                    results.append(result)
            except Exception as e:
                print(f"  EXCEPTION: {e}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "ocr_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    successful = len(results)
    total_chars = sum(r.get('chars', 0) for r in results)
    print(f"\nOCR Complete: {successful} PDFs, {total_chars} characters")
    return results


def convert_ocr_to_chunks(ocr_dir: Path, output_jsonl: Path):
    """Convert OCR text files to knowledge chunks."""
    txt_files = list(ocr_dir.rglob("*_ocr.txt"))
    print(f"Converting {len(txt_files)} OCR text files to chunks...")
    
    count = 0
    with open(output_jsonl, "w", encoding="utf-8") as out:
        for txt_file in txt_files:
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    text = f.read()
                
                if len(text.strip()) < 200:
                    continue
                
                # Classify domain
                domain, subdomain = classify_domain(text, str(txt_file))
                lang = detect_language(text)
                
                chunks = chunk_text(text)
                rel_path = txt_file.relative_to(ocr_dir).with_suffix('').with_suffix('')
                
                for i, chunk_str in enumerate(chunks):
                    chunk = KnowledgeChunk(
                        chunk_id=f"{rel_path}_ocr_chunk_{i:04d}",
                        source_file=f"{rel_path.name}.pdf",
                        source_path=str(txt_file).replace("_ocr.txt", ".pdf"),
                        file_type="pdf_ocr",
                        domain=domain,
                        subdomain=subdomain,
                        doc_type="advisory",
                        authority_tier=2,
                        language=lang,
                        title=f"{rel_path.name} - OCR part {i+1}",
                        content=chunk_str,
                        metadata={"pages": 1, "chunk_index": i, "ocr": True},
                        entities=extract_entities(chunk_str),
                        extracted_at=datetime.now().isoformat()
                    )
                    out.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
                    count += 1
            except Exception as e:
                print(f"Error converting {txt_file}: {e}")
    
    print(f"Created {count} OCR chunks -> {output_jsonl}")
    return count


def main():
    parser = argparse.ArgumentParser(description="Tesseract Batch OCR for Agricultural PDFs")
    parser.add_argument("--input", required=True, help="Input folder with PDFs")
    parser.add_argument("--output", required=True, help="Output folder for OCR results")
    parser.add_argument("--chunks", help="Output JSONL for chunks")
    parser.add_argument("--workers", type=int, default=2, help="Parallel workers")
    parser.add_argument("--convert-only", action="store_true", help="Only convert existing OCR txt to chunks")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if args.convert_only:
        count = convert_ocr_to_chunks(output_dir, Path(args.chunks))
        print(f"Converted {count} chunks")
        return
    
    # Step 1: OCR all PDFs
    results = batch_ocr(input_dir, output_dir, max_workers=args.workers)
    
    # Step 2: Convert to chunks
    if args.chunks:
        count = convert_ocr_to_chunks(output_dir, Path(args.chunks))
        print(f"Created {count} chunks -> {args.chunks}")


if __name__ == "__main__":
    import json
    import re
    from datetime import datetime
    main()