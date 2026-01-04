import json
import re

# Read the JSONL file
input_file = "jo_finetuning.jsonl"
output_file = "jo_finetuning.jsonl"

modified_count = 0
docs = []

# Read all documents
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line.strip())
        src_modified = False
        tgt_modified = False
        
        # Remove ", Page XX" from src_text
        if 'src_text' in doc and doc['src_text']:
            original_src = doc['src_text']
            doc['src_text'] = re.sub(r',\s*Page\s+\d+', '', doc['src_text'])
            if original_src != doc['src_text']:
                src_modified = True
        
        # Remove "الصفحة XX" from tgt_text
        if 'tgt_text' in doc and doc['tgt_text']:
            original_tgt = doc['tgt_text']
            doc['tgt_text'] = re.sub(r'،?\s*الصفحة\s+\d+', '', doc['tgt_text'])
            if original_tgt != doc['tgt_text']:
                tgt_modified = True
        
        if src_modified or tgt_modified:
            modified_count += 1
        
        docs.append(doc)

print(f"Total documents processed: {len(docs)}")
print(f"Documents modified: {modified_count}")

# Write back the modified documents
with open(output_file, 'w', encoding='utf-8') as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')

print(f"File updated successfully!")
