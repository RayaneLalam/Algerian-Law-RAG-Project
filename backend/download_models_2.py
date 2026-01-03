#!/usr/bin/env python3
"""
Robust Model Downloader for Algerian Law RAG Project
Uses huggingface_hub.snapshot_download for safer, resume-capable downloads.
"""

import os
import sys
from pathlib import Path

# SET HF_HOME BEFORE IMPORTING huggingface_hub
def setup_hf_cache():
    """Defines where the models will be saved."""
    # Current directory + /cache
    hf_home = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    os.environ['HF_HOME'] = hf_home
    Path(hf_home).mkdir(parents=True, exist_ok=True)
    print(f"📁 Cache Directory: {hf_home}")
    return hf_home

# Setup cache BEFORE importing huggingface_hub
setup_hf_cache()

# NOW import after HF_HOME is set
import logging
from huggingface_hub import snapshot_download

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the exact models we need
MODELS_TO_DOWNLOAD = [
    # "dangvantuan/sentence-camembert-large",
    # "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "bofenghuang/vigogne-2-7b-chat",
    "Qwen/Qwen2.5-7B-Instruct"
]
def main():
    logger.info("="*60)
    logger.info("  ALGERIAN LAW RAG - ROBUST MODEL DOWNLOADER")
    logger.info("="*60)
    
    failed_models = []
    
    for model_id in MODELS_TO_DOWNLOAD:
        logger.info(f"\n⬇️  Processing: {model_id}")
        try:
            # snapshot_download is safer: it fetches all files without running code
            # resume_download=True allows it to pick up where it left off
            path = snapshot_download(
                repo_id=model_id,
                force_download=True,
                resume_download=True,
                local_files_only=False
            )
            logger.info(f"   ✓ Success! Saved to: {path}")
            
            # Verify the model actually exists
            if os.path.exists(path):
                logger.info(f"   ✓ Verified: Model files exist at {path}")
            else:
                logger.error(f"   ✗ Verification failed: Path does not exist: {path}")
                failed_models.append(model_id)
            
        except Exception as e:
            logger.error(f"   ✗ Failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            failed_models.append(model_id)

    logger.info("\n" + "="*60)
    if failed_models:
        logger.error(f"⚠ The following models failed to download: {failed_models}")
        logger.error("Check your internet connection and try running the script again.")
        sys.exit(1)
    else:
        logger.info("✓ All models downloaded successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()