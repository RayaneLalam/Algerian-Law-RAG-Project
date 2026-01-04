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
        
        # Remove all variations of article numbers from src_text
        if 'src_text' in doc:
            original = doc['src_text']
            
            # Remove patterns like "Article XX:", "Article XX: (Modifié)", "Article XX: (Nouveau)" etc.
            doc['src_text'] = re.sub(r'^Article\s+\d+(?:\s+(?:bis|ter|quater))?:\s*(?:\([^)]*\))?\s*-?\s*', '', doc['src_text'])
            
            # Remove remaining article patterns
            doc['src_text'] = re.sub(r'^Article\s+\d+(?:\s+(?:bis|ter|quater))?:\s*', '', doc['src_text'])
            
            if original != doc['src_text']:
                modified_count += 1
        
        docs.append(doc)

print(f"Total documents processed: {len(docs)}")
print(f"Documents with article numbers removed: {modified_count}")

# Write back the cleaned documents
with open(output_file, 'w', encoding='utf-8') as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')

print(f"File updated successfully!")
