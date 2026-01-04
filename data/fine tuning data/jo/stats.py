import json
from collections import Counter

# Read the JSONL file
input_file = "jo_finetuning.jsonl"

src_text_counts = Counter()

# Read all documents and count src_text occurrences
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        doc = json.loads(line.strip())
        src_text = doc.get('src_text', '')
        src_text_counts[src_text] += 1

# Print statistics
print(f"Total unique src_text values: {len(src_text_counts)}")
print(f"Total documents: {sum(src_text_counts.values())}")
print(f"\n{'='*100}")
print(f"{'Count':<10} | {'src_text'}")
print(f"{'='*100}")

# Sort by count (descending)
for src_text, count in src_text_counts.most_common():
    print(f"{count:<10} | {src_text}")

print(f"\n{'='*100}")
print(f"\nMost common src_text values:")
for i, (src_text, count) in enumerate(src_text_counts.most_common(20), 1):
    print(f"{i}. [{count}] {src_text}")

print(f"\n{'='*100}")
print(f"\nLeast common src_text values:")
for i, (src_text, count) in enumerate(reversed(src_text_counts.most_common(20)), 1):
    print(f"{i}. [{count}] {src_text}")
