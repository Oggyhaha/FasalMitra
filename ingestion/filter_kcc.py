import json
from pathlib import Path

# Create a smaller, focused dataset
input_file = Path('extracted_chunks_kcc.jsonl')
output_file = Path('extracted_chunks_kcc_focused.jsonl')

# Priority crops for testing
priority_crops = {'cotton', 'सोयाबीन', 'soybean', 'wheat', 'गेहूं', 'rice', 'धान', 'mango', 'आम', 'tomato', 'टमाटर', 'chilli', 'मिर्च'}

# Hindi/Marathi keywords
hindi_keywords = ['खाद', 'उर्वरक', 'कीटनाशक', 'फवारणी', 'दवा', 'छिड़काव', 'बुआई', 'सिंचाई', 'बीज', 'किस्म', 'रोग', 'कीट', 'फसल', 'पानी', 'पाणी', 'उपज', 'उत्पादन']
marathi_keywords = ['खत', 'कीटकनाशक', 'फवारणी', 'औषध', 'बुआई', 'सिंचन', 'बियाणे', 'जात', 'रोग', 'कीड', 'पीक', 'पाणी', 'उत्पादन']

count = 0
kept = 0
with open('extracted_chunks_kcc.jsonl', 'r', encoding='utf-8') as infile, \
     open('extracted_chunks_kcc_focused.jsonl', 'w', encoding='utf-8') as outfile:
    
    for line in infile:
        if kept >= 50000:  # Limit to 50k chunks
            break
            
        chunk = json.loads(line)
        content = chunk.get('content', '').lower()
        crop = chunk.get('metadata', {}).get('crop', '').lower()
        
        # Check if relevant
        is_priority = any(c in crop for c in priority_crops)
        has_hindi = any(kw in content for kw in hindi_keywords)
        has_marathi = any(kw in content for kw in marathi_keywords)
        
        if is_priority or has_hindi or has_marathi:
            # Fix language detection
            devanagari = sum(1 for c in chunk.get('content', '') if '\u0900' <= c <= '\u097F')
            latin = sum(1 for c in chunk.get('content', '') if c.isascii() and c.isalpha())
            if devanagari > latin and devanagari > 10:
                chunk['language'] = 'hi'
            elif 'marathi' in chunk.get('content', '').lower() or 'मराठी' in chunk.get('content', '').lower():
                chunk['language'] = 'mr'
            else:
                chunk['language'] = 'en'
            
            # Fix domain
            crop_name = chunk.get('metadata', {}).get('crop', '').lower()
            if any(c in crop_name for c in ['livestock', 'cattle', 'dairy', 'poultry', 'goat', 'भैंस', 'गाय', 'मुर्गी']):
                chunk['domain'] = 'livestock'
            elif any(c in crop_name for c in ['mango', 'आम', 'banana', 'केला', 'fruit', 'फल']):
                chunk['domain'] = 'fruits'
            elif any(c in crop_name for c in ['vegetable', 'सब्जी', 'tomato', 'टमाटर', 'onion', 'potato']):
                chunk['domain'] = 'vegetables'
            
            outfile.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            kept += 1
            
        if kept % 5000 == 0:
            print(f'Kept {kept} chunks...')

print(f'Total kept: {kept}')