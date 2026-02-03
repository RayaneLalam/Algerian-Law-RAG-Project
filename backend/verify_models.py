#!/usr/bin/env python3
"""
Model Verification Script for Algerian Law RAG Project
Verifies that all required models are present in the local cache and usable offline.
"""

import os
import sys
import logging
from huggingface_hub import snapshot_download, try_to_load_from_cache
from huggingface_hub.utils import LocalEntryNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format for clean output
)
logger = logging.getLogger(__name__)

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# The exact list of models from your download script
REQUIRED_MODELS = [
    # Embedding Models
    "dangvantuan/sentence-camembert-large",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    
    # Generative Models (LLMs)
    "bofenghuang/vigogne-2-7b-chat",
    "Qwen/Qwen2.5-7B-Instruct"
]

def get_cache_path():
    """Points to the same './cache' folder used by the downloader."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')

def check_model(model_id, cache_dir):
    """
    Tries to locate the model snapshot in the local cache.
    Returns: (Success Boolean, Message String)
    """
    try:
        # local_files_only=True ensures we don't touch the internet
        snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            local_files_only=True
        )
        return True, "Present"
    except (LocalEntryNotFoundError, FileNotFoundError):
        return False, "MISSING"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    cache_dir = get_cache_path()
    
    print(f"\n{BOLD}ALGERIAN LAW RAG - CACHE VERIFICATION{RESET}")
    print(f"{BOLD}====================================={RESET}")
    print(f"📂 Checking Cache Directory: {cache_dir}\n")
    
    if not os.path.exists(cache_dir):
        print(f"{RED}⚠ CRITICAL: Cache directory not found!{RESET}")
        print(f"   Expected at: {cache_dir}")
        print("   Did you run 'download_models.py' first?")
        sys.exit(1)

    all_passed = True
    
    # Table Header
    print(f"{'MODEL ID':<60} | {'STATUS':<10}")
    print("-" * 75)

    for model in REQUIRED_MODELS:
        success, message = check_model(model, cache_dir)
        
        if success:
            status_text = f"{GREEN}✔ READY{RESET}"
        else:
            status_text = f"{RED}✗ {message}{RESET}"
            all_passed = False
            
        print(f"{model:<60} | {status_text}")

    print("-" * 75)
    
    if all_passed:
        print(f"\n{GREEN}SUCCESS: All models are verified and ready for offline use.{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}FAILURE: Some models are missing.{RESET}")
        print("Please rerun 'download_models.py' to fix the missing files.")
        sys.exit(1)

if __name__ == "__main__":
    main()