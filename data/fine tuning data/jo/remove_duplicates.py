import json
import random
from collections import defaultdict

# Read the JSONL file
input_file = "jo_finetuning.jsonl"
output_file = "jo_finetuning.jsonl"

# Group documents by src_text
docs_by_src = defaultdict(list)

# Read all documents and group by src_text
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line.strip())
        src_text = doc.get('src_text', '')
        docs_by_src[src_text].append(doc)

print(f"Total documents: {sum(len(docs) for docs in docs_by_src.values())}")
print(f"Total unique src_text values: {len(docs_by_src)}")

# Keep only 10% of documents from each src_text that appears more than once
filtered_docs = []
total_removed = 0

for src_text, docs in docs_by_src.items():
    if len(docs) > 1:
        # Keep 10% of these documents
        keep_count = max(1, len(docs) // 10)
        kept = random.sample(docs, keep_count)
        filtered_docs.extend(kept)
        total_removed += len(docs) - keep_count
        print(f"  '{src_text}' - had {len(docs)}, keeping {keep_count}, removing {len(docs) - keep_count}")
    else:
        # Keep all documents that appear only once
        filtered_docs.extend(docs)

print(f"\nTotal removed: {total_removed}")
print(f"Total documents after filtering: {len(filtered_docs)}")

# Shuffle and write back
random.shuffle(filtered_docs)

with open(output_file, 'w', encoding='utf-8') as f:
    for doc in filtered_docs:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')

print(f"File updated successfully!")
