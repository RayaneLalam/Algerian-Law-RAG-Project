import json

# Load both JSON files
with open('joradp_results_french_2023.json', 'r', encoding='utf-8') as f:
    french_data = json.load(f)

with open('joradp_results_arabic_2023.json', 'r', encoding='utf-8') as f:
    arabic_data = json.load(f)

# Create JSONL file with paired French-Arabic data by position
with open('jo_finetuning.jsonl', 'w', encoding='utf-8') as f:
    for i in range(len(french_data)):
        french_item = french_data[i]
        arabic_item = arabic_data[i]
        
        # Create multiple lines pairs for each field
        # Title pairing
        line1 = {
            "src_text": french_item['title'],
            "tgt_text": arabic_item['title']
        }
        f.write(json.dumps(line1, ensure_ascii=False) + '\n')
        
        # Institution pairing
        line2 = {
            "src_text": french_item['institution'],
            "tgt_text": arabic_item['institution']
        }
        f.write(json.dumps(line2, ensure_ascii=False) + '\n')
        
        # Journal reference pairing
        line3 = {
            "src_text": french_item['journal_ref'],
            "tgt_text": arabic_item['journal_ref']
        }
        f.write(json.dumps(line3, ensure_ascii=False) + '\n')
        
        # Summary pairing
        line4 = {
            "src_text": french_item['summary'],
            "tgt_text": arabic_item['summary']
        }
        f.write(json.dumps(line4, ensure_ascii=False) + '\n')

print("JSONL file created successfully: jo_finetuning.jsonl")
