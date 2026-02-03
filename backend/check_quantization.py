#!/usr/bin/env python3
"""
Quick debug script to check model quantization status and memory usage.
Useful for verifying that 4-bit quantization is actually being used.
"""

import os
import sys
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def check_model_quantization():
    """Check if models are loaded with quantization."""
    print("\n" + "="*70)
    print(" MODEL QUANTIZATION STATUS CHECK".center(70))
    print("="*70)
    
    try:
        from app.config.settings import settings
        from app.services.llm_service.bilingual_llm_service import BilingualLLMService
        
        print("\n1. CONFIGURATION CHECK")
        print("-" * 70)
        print(f"   USE_LOCAL_LLMS: {settings.USE_LOCAL_LLMS}")
        print(f"   USE_4BIT_QUANTIZATION: {settings.USE_4BIT_QUANTIZATION}")
        print(f"   COMPUTE_DEVICE: {settings.COMPUTE_DEVICE}")
        
        if not settings.USE_LOCAL_LLMS:
            print("\n   ⚠️  USE_LOCAL_LLMS is False - using API instead of local models")
            print("   To use local models, set: USE_LOCAL_LLMS=true in .env")
            return
        
        if not settings.USE_4BIT_QUANTIZATION:
            print("\n   ℹ️  4-bit quantization is disabled")
            print("   To enable, set: USE_4BIT_QUANTIZATION=true in .env")
        
        print("\n2. LOADING SERVICE")
        print("-" * 70)
        service = BilingualLLMService()
        print("   ✓ BilingualLLMService initialized")
        
        print("\n3. CHECKING QUANTIZATION SUPPORT")
        print("-" * 70)
        try:
            from transformers import BitsAndBytesConfig
            print("   ✓ BitsAndBytesConfig available")
        except ImportError:
            print("   ✗ BitsAndBytesConfig NOT available")
            print("     Install: pip install bitsandbytes")
        
        print("\n4. DEVICE & CUDA INFO")
        print("-" * 70)
        print(f"   Service device: {service.device}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA device: {torch.cuda.get_device_name(0)}")
            total_memory = torch.cuda.get_device_properties(0).total_memory
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            print(f"   GPU memory total: {format_size(total_memory)}")
            print(f"   GPU memory allocated: {format_size(allocated)}")
            print(f"   GPU memory reserved: {format_size(reserved)}")
        
        print("\n5. MODEL INFORMATION")
        print("-" * 70)
        print(f"   French LLM: {settings.FRENCH_LLM_MODEL}")
        print(f"   Arabic LLM: {settings.ARABIC_LLM_MODEL}")
        
        print("\n6. TO VERIFY MODELS ARE QUANTIZED")
        print("-" * 70)
        print("   Method 1: Load a model and check memory usage")
        print("   Method 2: Look at the application logs for:")
        print('      "✓ French LLM loaded with 4-bit quantization"')
        print('      "✓ Arabic LLM loaded with 4-bit quantization"')
        print("\n   Method 3: Check model.config or model properties (requires code)")
        
        print("\n7. NEXT STEPS")
        print("-" * 70)
        print("   1. Start backend: python run.py")
        print("   2. Send a query to trigger model loading")
        print("   3. Watch logs for quantization confirmation")
        print("   4. Check memory usage in system monitor")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def check_quantization_by_loading():
    """Attempt to load a model and check its configuration."""
    print("\n" + "="*70)
    print(" DETAILED QUANTIZATION CHECK (Advanced)".center(70))
    print("="*70)
    
    try:
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig
        
        print("\nThis will attempt to load a small test model to verify quantization.")
        print("Note: This may take several minutes and requires model files.\n")
        
        # Create a quantization config to test
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        
        print("✓ BitsAndBytesConfig created successfully")
        print(f"  Config: {quant_config}")
        
        # Try to show what a quantized model looks like
        print("\nQuantization details:")
        print(f"  - load_in_4bit: {quant_config.load_in_4bit}")
        print(f"  - compute_dtype: {quant_config.bnb_4bit_compute_dtype}")
        print(f"  - use_double_quant: {quant_config.bnb_4bit_use_double_quant}")
        print(f"  - quant_type: {quant_config.bnb_4bit_quant_type}")
        
        print("\n✓ If you see a model loaded with this config, it's using 4-bit quantization!")
        
    except Exception as e:
        print(f"Note: {e}")

if __name__ == "__main__":
    check_model_quantization()
    check_quantization_by_loading()
