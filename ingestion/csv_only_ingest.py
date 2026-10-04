import json
import pandas as pd
from pathlib import Path

output = open('extracted_chunks.jsonl', 'w', encoding='utf-8')
count = 0

base = Path(r'C:\FasalMitra\data\MIT-Project-Dataset')

# Process CSV files
csv_files = list(base.rglob('*.csv'))
print(f'Found {len(csv_files)} CSV files')

for f in csv_files:
    try:
        df = pd.read_csv(f, encoding_errors='ignore', low_memory=False)
        rows_per_chunk = 50
        total_rows = len(df)
        for start in range(0, total_rows, rows_per_chunk):
            end = min(start + rows_per_chunk, total_rows)
            chunk_df = df.iloc[start:end]
            content = chunk_df.to_string(index=False)
            summary = f"Dataset: {f.stem}\nColumns: {', '.join(df.columns.tolist())}\nRows: {total_rows}\nSample:\n{content[:2000]}"
            chunk = {
                'chunk_id': f'{f.stem}_rows_{start}_{end}',
                'source_file': f.name,
                'source_path': str(f),
                'file_type': 'csv',
                'domain': 'general',
                'subdomain': '',
                'doc_type': 'dataset',
                'authority_tier': 2,
                'language': 'en',
                'title': f'{f.stem} (rows {start+1}-{end})',
                'content': summary,
                'metadata': {'columns': df.columns.tolist(), 'total_rows': total_rows, 'row_range': f'{start+1}-{end}'},
                'entities': {},
                'extracted_at': '2026-10-03T00:00:00'
            }
            output.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            count += 1
        print(f'  {f.relative_to(base)}: {total_rows//rows_per_chunk + 1} chunks')
    except Exception as e:
        print(f'  Error: {e}')

# Process Excel files
xlsx_files = list(base.rglob('*.xlsx')) + list(base.rglob('*.xls'))
for f in xlsx_files:
    try:
        df = pd.read_excel(f)
        rows_per_chunk = 50
        total_rows = len(df)
        for start in range(0, total_rows, rows_per_chunk):
            end = min(start + rows_per_chunk, total_rows)
            chunk_df = df.iloc[start:end]
            content = chunk_df.to_string(index=False)
            summary = f"Dataset: {f.stem}\nColumns: {', '.join(df.columns.tolist())}\nRows: {total_rows}\nSample:\n{content[:2000]}"
            chunk = {
                'chunk_id': f'{f.stem}_rows_{start}_{end}',
                'source_file': f.name,
                'source_path': str(f),
                'file_type': 'xlsx',
                'domain': 'general',
                'subdomain': '',
                'doc_type': 'dataset',
                'authority_tier': 2,
                'language': 'en',
                'title': f'{f.stem} (rows {start+1}-{end})',
                'content': summary,
                'metadata': {'columns': df.columns.tolist(), 'total_rows': total_rows, 'row_range': f'{start+1}-{end}'},
                'entities': {},
                'extracted_at': '2026-10-03T00:00:00'
            }
            output.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            count += 1
        print(f'  {f.relative_to(base)}: {total_rows//rows_per_chunk + 1} chunks')
    except Exception as e:
        print(f'  Error: {e}')

output.close()
print(f'Total chunks: {count}')