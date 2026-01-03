#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# --- CONFIGURATION ---

# 1. Setup the cache directory explicitly
# We do this before importing huggingface_hub to ensure it uses this specific folder.
current_dir = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(current_dir, 'cache')
os.environ['HF_HOME'] = cache_dir
Path(cache_dir).mkdir(parents=True, exist_ok=True)

print(f"Cache directory set to: {cache_dir}")

# 2. Import the downloader
from huggingface_hub import snapshot_download

# 3. List of models to download
# COMMENT OUT lines with a '#' to skip models you do not want to check/download.
MODELS = [
    # Embedding Models
    # "dangvantuan/sentence-camembert-large",
    # "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",

    # LLMs (Generative Models)
    # "bofenghuang/vigogne-2-7b-chat",
    "Qwen/Qwen2.5-7B-Instruct"
]

def main():
    print("-" * 60)
    print("STARTING MODEL VERIFICATION AND DOWNLOAD")
    print("-" * 60)

    for model_id in MODELS:
        print(f"\nProcessing: {model_id}")
        print("Checking local cache and resuming download if necessary...")

        try:
            # snapshot_download automatically checks if files exist.
            # If they exist and match the server hash, it skips them.
            # If they are partial, it resumes.
            path = snapshot_download(
                repo_id=model_id,
                repo_type="model",
                resume_download=True,
                local_files_only=False # Allow internet connection to complete files
            )
            
            print(f"STATUS: Complete.")
            print(f"LOCATION: {path}")

        except Exception as e:
            print(f"STATUS: Failed.")
            print(f"ERROR: {str(e)}")

    print("-" * 60)
    print("Process finished.")

if __name__ == "__main__":
    main()