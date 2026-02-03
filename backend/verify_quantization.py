#!/usr/bin/env python3
"""
Verification script to check if 4-bit quantization is properly enabled for models.
Run this script to verify your quantization setup.
"""

import os
import sys
import torch
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check environment setup for quantization."""
    print("\n" + "="*60)
    print("ENVIRONMENT CHECK")
    print("="*60)
    
    print(f"✓ Python version: {sys.version.split()[0]}")
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"✓ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    print(f"\n✓ USE_4BIT_QUANTIZATION env: {os.getenv('USE_4BIT_QUANTIZATION', 'Not set')}")
    print(f"✓ COMPUTE_DEVICE env: {os.getenv('COMPUTE_DEVICE', 'Not set')}")
    
    return True


def check_settings():
    """Check settings from configuration."""
    print("\n" + "="*60)
    print("SETTINGS CHECK")
    print("="*60)
    
    try:
        from app.config.settings import settings
        
        print(f"✓ USE_LOCAL_LLMS: {settings.USE_LOCAL_LLMS}")
        print(f"✓ USE_4BIT_QUANTIZATION: {settings.USE_4BIT_QUANTIZATION}")
        print(f"✓ COMPUTE_DEVICE: {settings.COMPUTE_DEVICE}")
        print(f"✓ FRENCH_LLM_MODEL: {settings.FRENCH_LLM_MODEL}")
        print(f"✓ ARABIC_LLM_MODEL: {settings.ARABIC_LLM_MODEL}")
        print(f"✓ DEFAULT_LLM_MODEL: {settings.DEFAULT_LLM_MODEL}")
        
        return settings
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        return None


def check_transformers_quantization():
    """Check if transformers library supports quantization."""
    print("\n" + "="*60)
    print("TRANSFORMERS QUANTIZATION SUPPORT")
    print("="*60)
    
    try:
        from transformers import BitsAndBytesConfig
        print("✓ BitsAndBytesConfig available")
        
        # Try to create a quantization config
        try:
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            print("✓ BitsAndBytesConfig created successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to create BitsAndBytesConfig: {e}")
            return False
    except ImportError:
        print("✗ BitsAndBytesConfig not available. Install: pip install bitsandbytes")
        return False


def check_model_loading_logic():
    """Check the model loading logic in BilingualLLMService."""
    print("\n" + "="*60)
    print("MODEL LOADING LOGIC CHECK")
    print("="*60)
    
    try:
        from app.services.llm_service.bilingual_llm_service import BilingualLLMService
        
        service = BilingualLLMService()
        print(f"✓ BilingualLLMService initialized")
        print(f"  - use_local_llms: {service.use_local_llms}")
        print(f"  - device: {service.device}")
        print(f"  - settings.USE_4BIT_QUANTIZATION: {service.settings.USE_4BIT_QUANTIZATION}")
        
        # Check quantization logic
        should_use_quant = service.settings.USE_4BIT_QUANTIZATION
        print(f"\n✓ Quantization will be attempted: {should_use_quant}")
        
        if should_use_quant:
            print("  ✓ 4-bit quantization is ENABLED in configuration")
            print("  → Models will attempt to load with 4-bit quantization")
            print("  → If CUDA is not available, it will fallback gracefully")
        else:
            print("  ✗ 4-bit quantization is DISABLED")
            print("  → To enable: set USE_4BIT_QUANTIZATION=true in .env")
        
        return should_use_quant
    except Exception as e:
        print(f"✗ Error checking model loading logic: {e}")
        return False


def create_test_model_load():
    """Create a test to verify model loading with quantization."""
    print("\n" + "="*60)
    print("MODEL LOADING TEST (OPTIONAL)")
    print("="*60)
    
    try:
        from app.services.llm_service.bilingual_llm_service import BilingualLLMService
        import logging
        
        # Enable logging to see what's happening
        logging.basicConfig(level=logging.INFO)
        
        print("\nTo test model loading, you can run:")
        print("  from app.services.llm_service.bilingual_llm_service import BilingualLLMService")
        print("  service = BilingualLLMService()")
        print("  # This will trigger model loading on first use")
        print("  response = service.generate_completion('Hello', language='en')")
        print("\nWatch the logs for:")
        print("  ✓ 'Attempting to load ... with 4-bit quantization...'")
        print("  ✓ '✓ ... LLM loaded with 4-bit quantization'")
        return True
    except Exception as e:
        print(f"Note: {e}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print(" QUANTIZATION VERIFICATION SCRIPT".center(70))
    print("="*70)
    
    checks = {
        "Environment": check_environment,
        "Settings": check_settings,
        "Transformers": check_transformers_quantization,
        "Model Loading Logic": check_model_loading_logic,
        "Test Model Load": create_test_model_load,
    }
    
    results = {}
    for name, check_fn in checks.items():
        try:
            results[name] = check_fn() is not False
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    print("""
1. VERIFY .env FILE
   - Ensure USE_4BIT_QUANTIZATION=true is set
   - Ensure USE_LOCAL_LLMS=true is set
   
2. CHECK ENVIRONMENT
   - Install bitsandbytes: pip install bitsandbytes
   - For GPU: bitsandbytes with CUDA support
   - For CPU: bitsandbytes also works but is slower

3. RUN YOUR APPLICATION
   - Start the backend: python run.py
   - Watch the logs during model loading
   - You should see: "✓ French LLM loaded with 4-bit quantization"
   
4. VERIFY IN LOGS
   Look for these log messages confirming quantization:
   - "Attempting to load [Model] with 4-bit quantization..."
   - "✓ [Model] LLM loaded with 4-bit quantization"
   
   If you see fallback messages like "Falling back to regular loading",
   check your bitsandbytes installation or CUDA setup.
""")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
