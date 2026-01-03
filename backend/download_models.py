#!/usr/bin/env python3
"""
Model Pre-download Script for Algerian Law RAG Project

This script pre-downloads all AI models needed by the application into the local
Hugging Face cache. This prevents the application from attempting to download models
at runtime and ensures all dependencies are available when moving to a new machine.

Models to download:
- Embedding Models (Sentence Transformers):
  * dangvantuan/sentence-camembert-large (French embeddings)
  * sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (Multilingual fallback)

- Generative Models (LLMs):
  * bofenghuang/vigogne-2-7b-chat (French LLM)
  * Qwen/Qwen2.5-7B-Instruct (Arabic LLM)

Usage:
    python download_models.py [--device cuda|cpu] [--skip-quantization]

Examples:
    # Download models for CPU only (recommended for initial setup)
    python download_models.py --device cpu
    
    # Download models for GPU
    python download_models.py --device cuda
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_hf_cache():
    """Ensure Hugging Face cache directory exists and is properly configured."""
    hf_home = os.path.join(os.path.dirname(__file__), 'cache')
    os.environ['HF_HOME'] = hf_home
    Path(hf_home).mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Hugging Face cache directory: {hf_home}")
    return hf_home


def download_embedding_models(device: str = 'cpu'):
    """Download all embedding models used in the application."""
    logger.info("\n" + "="*70)
    logger.info("DOWNLOADING EMBEDDING MODELS")
    logger.info("="*70)
    
    from sentence_transformers import SentenceTransformer
    
    embedding_models = [
        {
            'name': 'dangvantuan/sentence-camembert-large',
            'description': 'French-specific sentence embeddings (CamemBERT)',
            'use_case': 'French legal document embeddings'
        },
        {
            'name': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            'description': 'Multilingual embeddings (lightweight)',
            'use_case': 'Fallback multilingual embeddings'
        }
    ]
    
    successful = []
    failed = []
    
    for model_info in embedding_models:
        model_name = model_info['name']
        description = model_info['description']
        use_case = model_info['use_case']
        
        try:
            logger.info(f"\n📥 Downloading: {model_name}")
            logger.info(f"   Description: {description}")
            logger.info(f"   Use case: {use_case}")
            
            # Load the model (this will download it to cache)
            model = SentenceTransformer(model_name, device=device)
            
            logger.info(f"   ✓ Successfully downloaded and cached")
            logger.info(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
            successful.append(model_name)
            
        except Exception as e:
            logger.error(f"   ✗ Failed to download: {str(e)}")
            failed.append((model_name, str(e)))
    
    return successful, failed


def download_llm_models(device: str = 'cpu', skip_quantization: bool = False):
    """Download all LLM models used in the application."""
    logger.info("\n" + "="*70)
    logger.info("DOWNLOADING GENERATIVE MODELS (LLMs)")
    logger.info("="*70)
    
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    llm_models = [
        {
            'name': 'bofenghuang/vigogne-2-7b-chat',
            'description': 'Vigogne 2 - French instruction-tuned LLM (7B parameters)',
            'use_case': 'French legal question answering',
            'type': 'causal_lm'
        },
        {
            'name': 'Qwen/Qwen2.5-7B-Instruct',
            'description': 'Qwen 2.5 - Multilingual instruction-tuned LLM (7B parameters)',
            'use_case': 'Arabic legal question answering',
            'type': 'causal_lm'
        }
    ]
    
    successful = []
    failed = []
    
    for model_info in llm_models:
        model_name = model_info['name']
        description = model_info['description']
        use_case = model_info['use_case']
        
        try:
            logger.info(f"\n📥 Downloading: {model_name}")
            logger.info(f"   Description: {description}")
            logger.info(f"   Use case: {use_case}")
            logger.info(f"   Size: ~14GB (7B parameters)")
            
            # Download tokenizer
            logger.info("   Downloading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger.info("   ✓ Tokenizer cached")
            
            # Download model
            logger.info("   Downloading model weights...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=("auto" if device == 'cuda' else None),
                torch_dtype=("auto" if device == 'cuda' else None),
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            logger.info("   ✓ Model weights cached")
            logger.info(f"   Model type: {model_info['type']}")
            
            successful.append(model_name)
            
        except Exception as e:
            logger.error(f"   ✗ Failed to download: {str(e)}")
            failed.append((model_name, str(e)))
    
    return successful, failed


def print_summary(embedding_success: List[str], embedding_failed: List[Tuple],
                  llm_success: List[str], llm_failed: List[Tuple]):
    """Print a summary of the download results."""
    logger.info("\n" + "="*70)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*70)
    
    total_success = len(embedding_success) + len(llm_success)
    total_failed = len(embedding_failed) + len(llm_failed)
    
    logger.info(f"\n✓ Successfully downloaded: {total_success} models")
    
    if embedding_success:
        logger.info("\n  Embedding Models:")
        for model in embedding_success:
            logger.info(f"    ✓ {model}")
    
    if llm_success:
        logger.info("\n  Generative Models (LLMs):")
        for model in llm_success:
            logger.info(f"    ✓ {model}")
    
    if total_failed > 0:
        logger.warning(f"\n✗ Failed to download: {total_failed} models")
        
        if embedding_failed:
            logger.warning("\n  Embedding Models:")
            for model, error in embedding_failed:
                logger.warning(f"    ✗ {model}")
                logger.warning(f"      Error: {error}")
        
        if llm_failed:
            logger.warning("\n  Generative Models (LLMs):")
            for model, error in llm_failed:
                logger.warning(f"    ✗ {model}")
                logger.warning(f"      Error: {error}")
    
    cache_dir = os.environ.get('HF_HOME', os.path.expanduser('~/.cache/huggingface/hub'))
    logger.info(f"\n📁 Models are cached at: {cache_dir}")
    
    logger.info("\n" + "="*70)
    if total_failed == 0:
        logger.info("✓ All models downloaded successfully!")
        logger.info("The application can now run without internet access.")
    else:
        logger.warning(f"⚠ {total_failed} model(s) failed to download.")
        logger.warning("Please check the errors above and try again.")
    logger.info("="*70 + "\n")
    
    return total_failed == 0


def main():
    """Main function to orchestrate model downloads."""
    parser = argparse.ArgumentParser(
        description='Pre-download all AI models for the Algerian Law RAG Project',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--device',
        choices=['cuda', 'cpu'],
        default='cpu',
        help='Device to use for model loading (default: cpu)'
    )
    
    parser.add_argument(
        '--skip-quantization',
        action='store_true',
        help='Skip 4-bit quantization settings'
    )
    
    args = parser.parse_args()
    
    logger.info("\n" + "="*70)
    logger.info("ALGERIAN LAW RAG - MODEL PRE-DOWNLOAD SCRIPT")
    logger.info("="*70)
    logger.info(f"Device: {args.device.upper()}")
    logger.info(f"Skip quantization: {args.skip_quantization}")
    
    try:
        # Setup cache
        hf_cache = setup_hf_cache()
        
        # Download embedding models
        embedding_success, embedding_failed = download_embedding_models(device=args.device)
        
        # Download LLM models
        llm_success, llm_failed = download_llm_models(
            device=args.device,
            skip_quantization=args.skip_quantization
        )
        
        # Print summary
        success = print_summary(
            embedding_success, embedding_failed,
            llm_success, llm_failed
        )
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Download interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n\n✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
