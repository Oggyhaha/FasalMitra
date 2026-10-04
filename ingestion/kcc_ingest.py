import json
import pandas as pd
from pathlib import Path

def create_kcc_chunks(df, source_file, source_path, base_path):
    """Create one chunk per KCC call (Q&A pair)"""
    chunks = []
    
    # Find relevant columns (case insensitive)
    cols = {c.lower(): c for c in df.columns}
    
    # Map common column names
    query_col = cols.get('querytext') or cols.get('query') or cols.get('question')
    answer_col = cols.get('kccans') or cols.get('answer') or cols.get('advice')
    crop_col = cols.get('crop') or cols.get('sector')
    district_col = cols.get('districtname') or cols.get('district')
    state_col = cols.get('statename') or cols.get('state')
    season_col = cols.get('season')
    querytype_col = cols.get('querytype') or cols.get('type')
    category_col = cols.get('category')
    block_col = cols.get('blockname')
    created_col = cols.get('createdon')
    
    print(f"  Columns found: query={query_col}, answer={answer_col}, crop={crop_col}, district={district_col}")
    
    if not answer_col:
        print(f"  WARNING: No answer column found in {source_file}")
        return []
    
    for idx, row in df.iterrows():
        answer = str(row[answer_col]).strip() if pd.notna(row[answer_col]) else ""
        query = str(row[query_col]).strip() if query_col and pd.notna(row[query_col]) else ""
        
        # Skip if no meaningful answer
        if len(answer) < 20:
            continue
            
        crop = str(row[crop_col]).strip() if crop_col and pd.notna(row[crop_col]) else "General"
        district = str(row[district_col]).strip() if district_col and pd.notna(row[district_col]) else ""
        state = str(row[state_col]).strip() if state_col and pd.notna(row[state_col]) else ""
        
        # Determine domain from crop
        crop_lower = crop.lower()
        if any(c in crop_lower for c in ['cotton', 'कपास', 'kapas']):
            domain = "crops"
        elif any(c in crop_lower for c in ['soybean', 'सोयाबीन', 'soya']):
            domain = "crops"
        elif any(c in crop_lower for c in ['wheat', 'गेहूं', 'wheat']):
            domain = "crops"
        elif any(c in crop_lower for c in ['rice', 'धान', 'paddy', 'rice']):
            domain = "crops"
        elif any(c in crop_lower for c in ['livestock', 'cattle', 'dairy', 'poultry', 'goat', 'भैंस', 'गाय', 'मुर्गी']):
            domain = "livestock"
        elif any(c in crop_lower for c in ['mango', 'आम', 'banana', 'केला', 'fruit', 'फल']):
            domain = "fruits"
        else:
            domain = "crops"
        
        # Determine language from answer text
        answer_text = answer
        devanagari = sum(1 for c in answer if '\u0900' <= c <= '\u097F')
        latin = sum(1 for c in answer if c.isascii() and c.isalpha())
        language = "hi" if devanagari > latin else "en"
        
        # Create content with Q&A format
        content = f"Farmer Question: {query}\nExpert Advice: {answer}" if query else f"Expert Advice: {answer}"
        
        chunk = {
            'chunk_id': f'{Path(source_file).stem}_kcc_{idx}',
            'source_file': Path(source_file).name,
            'source_path': str(source_path),
            'file_type': 'csv',
            'domain': domain,
            'subdomain': '',
            'doc_type': 'kcc_advisory',
            'authority_tier': 1,  # KCC is authoritative
            'language': language,
            'title': f'KCC Advisory: {crop} - {answer[:50]}...',
            'content': content,
            'metadata': {
                'crop': crop,
                'district': district,
                'state': state,
                'query_type': str(row[querytype_col]).strip() if querytype_col and pd.notna(row[querytype_col]) else '',
                'category': str(row[category_col]).strip() if category_col and pd.notna(row[category_col]) else '',
                'block': str(row[block_col]).strip() if block_col and pd.notna(row[block_col]) else '',
                'created_on': str(row[created_col]).strip() if created_col and pd.notna(row[created_col]) else '',
            },
            'entities': {},
            'extracted_at': '2026-10-03T00:00:00'
        }
        chunks.append(chunk)
    
    return chunks

def process_csv_files():
    output = open('extracted_chunks_kcc.jsonl', 'w', encoding='utf-8')
    count = 0
    
    base = Path(r'C:\FasalMitra\data\MIT-Project-Dataset')
    csv_files = list(base.rglob('*.csv'))
    print(f'Found {len(csv_files)} CSV files')
    
    total_chunks = 0
    for f in csv_files:
        try:
            df = pd.read_csv(f, encoding_errors='ignore', low_memory=False)
            chunks = create_kcc_chunks(df, f.name, f, base)
            
            for chunk in chunks:
                output.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                total_chunks += 1
            
            print(f'  {f.relative_to(base)}: {len(chunks)} KCC chunks created')
        except Exception as e:
            print(f'  Error processing {f}: {e}')
    
    output.close()
    print(f'Total KCC chunks: {total_chunks}')

if __name__ == "__main__":
    process_csv_files()