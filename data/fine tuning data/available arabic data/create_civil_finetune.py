import json

# Read the files
code_civil_file = "code_civil_chunks_complete.json"
algerian_civil_file = "algerian_civil_code_cleaned.json"
output_file = "civil_finetune.jsonl"

# Load code_civil_chunks_complete.json
with open(code_civil_file, 'r', encoding='utf-8') as f:
    code_civil_data = json.load(f)

# Load algerian_civil_code_cleaned.json
with open(algerian_civil_file, 'r', encoding='utf-8') as f:
    algerian_data = json.load(f)

# Extract first 50 articles from each
code_civil_chunks = code_civil_data[:50] if isinstance(code_civil_data, list) else []
algerian_articles = algerian_data.get('articles', [])[:50] if isinstance(algerian_data, dict) else algerian_data[:50]

print(f"Code civil chunks loaded: {len(code_civil_chunks)}")
print(f"Algerian civil articles loaded: {len(algerian_articles)}")

# Create pairs and write to JSONL
paired_count = 0
with open(output_file, 'w', encoding='utf-8') as f:
    for i in range(min(len(code_civil_chunks), len(algerian_articles))):
        src_text = code_civil_chunks[i].get('content', '')
        tgt_text = algerian_articles[i].get('text', '')
        
        if src_text and tgt_text:
            doc = {
                "src_text": src_text,
                "tgt_text": tgt_text,
                "src_article": code_civil_chunks[i].get('article_number', ''),
                "tgt_article": algerian_articles[i].get('article', ''),
                "src_file": "code_civil_chunks_complete.json",
                "tgt_file": "algerian_civil_code_cleaned.json"
            }
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            paired_count += 1

print(f"Total paired documents created: {paired_count}")
print(f"File '{output_file}' created successfully!")
