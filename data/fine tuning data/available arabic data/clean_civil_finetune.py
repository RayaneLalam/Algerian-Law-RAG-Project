import json
import re

# Read the JSONL file
input_file = "civil_finetune.jsonl"
output_file = "civil_finetune.jsonl"

modified_count = 0
docs = []

# Read all documents
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line.strip())
        
        # Remove article numbers and annotations from src_text
        # Pattern: "Article XX: (Modifié) -" or "Article XX: -" or similar
        if 'src_text' in doc:
            doc['src_text'] = re.sub(r'^Article\s+\d+:\s*\(?Modifié\)?\s*-?\s*', '', doc['src_text'])
            doc['src_text'] = re.sub(r'^Article\s+\d+:\s*\(?Nouveau\)?\s*-?\s*', '', doc['src_text'])
            doc['src_text'] = re.sub(r'^Article\s+\d+\s+bis:\s*\(?Nouveau\)?\s*-?\s*', '', doc['src_text'])
            doc['src_text'] = re.sub(r'^Article\s+\d+\s+ter:\s*\(?Nouveau\)?\s*-?\s*', '', doc['src_text'])
            doc['src_text'] = re.sub(r'^Article\s+\d+\s+quater:\s*\(?Nouveau\)?\s*-?\s*', '', doc['src_text'])
        
        # Remove the metadata attributes
        doc.pop('src_article', None)
        doc.pop('tgt_article', None)
        doc.pop('src_file', None)
        doc.pop('tgt_file', None)
        
        docs.append(doc)
        modified_count += 1

print(f"Total documents processed: {len(docs)}")
print(f"Documents cleaned: {modified_count}")

# Write back the cleaned documents
with open(output_file, 'w', encoding='utf-8') as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')

print(f"File updated successfully!")
