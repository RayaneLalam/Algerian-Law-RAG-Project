import json
import random
from pathlib import Path

# File paths
train_file = "fine_tuning_data_train.jsonl"
val_file = "fine_tuning_data_val.jsonl"
num_samples = 31

# Read all training data
train_data = []
with open(train_file, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        if line.strip():  # Skip empty lines
            try:
                train_data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠ Skipping line {line_num}: {e}")

print(f"Total training samples: {len(train_data)}")

# Randomly select 31 samples
selected_indices = random.sample(range(len(train_data)), num_samples)
selected_samples = [train_data[i] for i in selected_indices]

# Create remaining training data (without selected samples)
remaining_data = [train_data[i] for i in range(len(train_data)) if i not in selected_indices]

# Write selected samples to validation file (append if exists)
with open(val_file, 'a', encoding='utf-8') as f:
    for sample in selected_samples:
        f.write(json.dumps(sample, ensure_ascii=False) + '\n')

# Write remaining data back to training file
with open(train_file, 'w', encoding='utf-8') as f:
    for sample in remaining_data:
        f.write(json.dumps(sample, ensure_ascii=False) + '\n')

print(f"✓ Moved {num_samples} samples to {val_file}")
print(f"✓ Remaining training samples: {len(remaining_data)}")
