#!/usr/bin/env python3
"""
GPU-Accelerated OCR Pipeline for Scanned Agricultural PDFs
Uses PaddleOCR with RTX 3050 GPU for fast processing
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF

try:
    from paddleocr import PaddleOCR
except ImportError:
    os.system("pip install paddleocr -q")
    from paddleocr import PaddleOCR

try:
    from pdf2image import convert_from_path
except ImportError:
    os.system("pip install pdf2image -q")
    from pdf2image import convert_from_path

# PaddleOCR with GPU - will auto-detect CUDA
# For RTX 3050: use_gpu=True, gpu_mem=4000 (4GB VRAM)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',  # Supports: en, ch, french, german, korean, japan, etc.
    use_gpu=True,
    gpu_mem=4000,
    show_log=False,
    enable_mkldnn=False,
    use_tensorrt=False,
    precision='fp16'  # Half precision for speed on RTX 3050
)

# Also support Hindi/Marathi
ocr_hi = PaddleOCR(
    use_angle_cls=True,
    lang='hindi',
    use_gpu=True,
    gpu_mem=4000,
    show_log=False,
    precision='fp16'
)

# Marathi (use 'latin' or try 'ta' for Tamil script similarity)
ocr_mr = PaddleOCR(
    use_angle_cls=True,
    lang='latin',  # Works for Devanagari-based scripts too
    use_gpu=True,
    gpu_mem=4000,
    show_log=False,
    precision='fp16'
)


def pdf_to_images(pdf_path: Path, dpi: int = 200) -> List:
    """Convert PDF pages to images using PyMuPDF (faster than pdf2image)."""
    try:
        doc = fitz.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render at 200 DPI for good OCR quality
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img = pix.tobytes("ppm")
            images.append((page_num, img))
        doc.close()
        return images
    except Exception as e:
        print(f"  PyMuPDF error: {e}")
        return []


def ocr_image(image_bytes: bytes, lang: str = 'en') -> str:
    """Run OCR on image bytes."""
    try:
        # Save to temp file for PaddleOCR
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            if lang == 'hi':
                result = ocr_hi.ocr(tmp_path, cls=True)
            elif lang == 'mr':
                result = ocr_mr.ocr(tmp_path, cls=True)
            else:
                result = ocr.ocr(tmp_path, cls=True)
            
            # Extract text
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        texts.append(line[1][0])
            return "\n".join(texts)
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        return f"OCR_ERROR: {e}"


def process_pdf_ocr(pdf_path: Path, output_dir: Path = None) -> Dict:
    """Process a single PDF with OCR."""
    print(f"  Processing: {pdf_path.name}")
    
    images = pdf_to_images(pdf_path, dpi=200)
    if not images:
        return {"success": False, "error": "No images extracted"}
    
    all_text = []
    for page_num, img_bytes in images:
        # Try English first
        text = ocr_image(img_bytes, 'en')
        if len(text.strip()) < 50:  # Low confidence, try Hindi
            text = ocr_image(img_bytes, 'hi')
        if len(text.strip()) < 50:  # Try Marathi
            text = ocr_image(img_bytes, 'mr')
        
        if text and not text.startswith("OCR_ERROR"):
            all_text.append(f"--- Page {page_num+1} ---\n{text}")
    
    full_text = "\n\n".join(all_text)
    
    # Save OCR text
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        txt_file = output_dir / f"{pdf_path.stem}_ocr.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(full_text)
    
    return {
        "success": True,
        "pages": len(images),
        "text": full_text,
        "chars": len(full_text)
    }


def batch_ocr_pdfs(input_dir: Path, output_dir: Path, max_workers: int = 2):
    """Process all scanned PDFs in directory with parallel OCR."""
    
    # Find all PDFs
    pdf_files = list(input_dir.rglob("*.pdf"))
    
    # Filter: only process PDFs that haven't been OCR'd or have no text
    # (You can also pass a list of known scanned PDFs)
    print(f"Found {len(pdf_files)} PDF files")
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_pdf_ocr, pdf, output_dir): pdf for pdf in pdf_files}
        
        for future in as_completed(futures):
            pdf = futures[future]
            try:
                result = future.result()
                result['file'] = str(pdf.relative_to(input_dir))
                results.append(result)
                if result['success']:
                    print(f"  OK {pdf.name}: {result['pages']} pages, {result['chars']} chars")
                else:
                    print(f"  FAIL {pdf.name}: {result.get('error')}")
            except Exception as e:
                print(f"  EXCEPTION {pdf.name}: {e}")
                results.append({"file": str(pdf), "success": False, "error": str(e)})
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "ocr_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    successful = sum(1 for r in results if r.get('success'))
    total_chars = sum(r.get('chars', 0) for r in results)
    print(f"\nCompleted: {successful}/{len(pdf_files)} PDFs, {total_chars} total characters")
    return results


def convert_ocr_to_chunks(ocr_results_dir: Path, output_jsonl: Path):
    """Convert OCR text files to knowledge chunks."""
    txt_files = list(ocr_results_dir.rglob("*_ocr.txt"))
    print(f"Converting {len(txt_files)} OCR text files to chunks...")
    
    count = 0
    with open(output_jsonl, "w", encoding="utf-8") as out:
        for txt_file in txt_files:
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    text = f.read()
                
                if len(text.strip()) < 200:
                    continue
                
                # Simple chunking
                chunks = chunk_text(text)
                rel_path = txt_file.relative_to(ocr_results_dir).with_suffix('').with_suffix('')
                
                for i, chunk_text in enumerate(chunks):
                    chunk = {
                        "chunk_id": f"{rel_path}_ocr_chunk_{i:04d}",
                        "source_file": f"{rel_path.name}.pdf",
                        "source_path": str(txt_file).replace("_ocr.txt", ".pdf"),
                        "file_type": "pdf_ocr",
                        "domain": "crops",  # Will be reclassified later
                        "subdomain": "",
                        "doc_type": "advisory",
                        "authority_tier": 2,
                        "language": "en",
                        "title": f"{rel_path.name} - OCR part {i+1}",
                        "content": chunk_text,
                        "metadata": {"pages": 1, "chunk_index": i, "ocr": True},
                        "entities": {},
                        "extracted_at": datetime.now().isoformat()
                    }
                    out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    count += 1
            except Exception as e:
                print(f"Error converting {txt_file}: {e}")
    
    print(f"Created {count} OCR chunks -> {output_jsonl}")
    return count


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


def main():
    parser = argparse.ArgumentParser(description="GPU OCR for scanned agricultural PDFs")
    parser.add_argument("--input", required=True, help="Input folder with PDFs")
    parser.add_argument("--output", required=True, help="Output folder for OCR results")
    parser.add_argument("--chunks", help="Output JSONL for chunks")
    parser.add_argument("--workers", type=int, default=2, help="Parallel workers (GPU memory limited)")
    parser.add_argument("--convert-only", action="store_true", help="Only convert existing OCR txt to chunks")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if args.convert_only:
        count = convert_ocr_to_chunks(output_dir, Path(args.chunks))
        print(f"Converted {count} chunks")
        return
    
    # Step 1: OCR all PDFs
    results = batch_ocr_pdfs(input_dir, output_dir, max_workers=args.workers)
    
    # Step 2: Convert to chunks
    if args.chunks:
        count = convert_ocr_to_chunks(output_dir, Path(args.chunks))
        print(f"Created {count} chunks -> {args.chunks}")


if __name__ == "__main__":
    import re
    main()