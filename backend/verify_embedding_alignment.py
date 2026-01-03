#!/usr/bin/env python3
"""
Embedding Alignment Verification Script

Critical Fix #1: Verify that embedding models used in backend service 
match exactly with what was used in the notebook to create FAISS indices.

This prevents garbage retrieval that can cause hallucinations.
"""

import os
import sys
import json
import faiss
import torch
from pathlib import Path

def check_embedding_alignment():
    """Verify embedding model alignment between notebook and backend."""
    
    print("=" * 60)
    print("🔍 CRITICAL FIX #1: Embedding Alignment Verification")
    print("=" * 60)
    
    # From notebook: billangual-pipeline.ipynb 
    notebook_models = {
        'french': 'dangvantuan/sentence-camembert-large',
        'arabic': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    }
    
    # From backend settings
    sys.path.append('/media/maria/DATA/4th year/sem1/NLP/project/git/Algerian-Law-RAG-Project/backend')
    from app.config.settings import settings
    
    backend_models = {
        'french': settings.FRENCH_EMBEDDING_MODEL,
        'arabic': settings.ARABIC_EMBEDDING_MODEL
    }
    
    print(f"📓 Notebook French Model: {notebook_models['french']}")
    print(f"⚙️  Backend French Model:  {backend_models['french']}")
    french_match = notebook_models['french'] == backend_models['french']
    print(f"✅ French Match: {french_match}")
    
    print(f"\n📓 Notebook Arabic Model: {notebook_models['arabic']}")  
    print(f"⚙️  Backend Arabic Model:  {backend_models['arabic']}")
    arabic_match = notebook_models['arabic'] == backend_models['arabic']
    print(f"✅ Arabic Match: {arabic_match}")
    
    if french_match and arabic_match:
        print("\n🎯 SUCCESS: All embedding models match between notebook and backend!")
        print("   This ensures consistent retrieval and prevents garbage results.")
        return True
    else:
        print("\n❌ CRITICAL ERROR: Embedding model mismatch detected!")
        print("   This can cause garbage retrieval and Chinese character hallucination!")
        return False

def check_faiss_dimensions():
    """Check FAISS index dimensions match expected embedding dimensions."""
    
    print("\n" + "=" * 60)
    print("📏 DIMENSION CHECK: FAISS Index vs Expected Embedding Dims")
    print("=" * 60)
    
    # FAISS index paths (relative from project root)
    french_index_path = "../data/faiss/algerian_legal(jo+constitution+penale+civil+commerce+famille) embedder_ dangvantuan-sentence-camembert-large.faiss"
    arabic_index_path = "../data/faiss/laws_ar.index"
    
    # Expected dimensions from notebook
    expected_dims = {
        'french': 1024,  # dangvantuan/sentence-camembert-large
        'arabic': 384    # sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    }
    
    # Check French index
    if os.path.exists(french_index_path):
        try:
            french_index = faiss.read_index(french_index_path)
            french_actual_dim = french_index.d
            print(f"🇫🇷 French FAISS Index Dimensions: {french_actual_dim}")
            print(f"🎯 Expected French Dimensions: {expected_dims['french']}")
            french_dim_match = french_actual_dim == expected_dims['french']
            print(f"✅ French Dimension Match: {french_dim_match}")
        except Exception as e:
            print(f"❌ Error loading French index: {e}")
            french_dim_match = False
    else:
        print(f"❌ French index not found: {french_index_path}")
        french_dim_match = False
    
    # Check Arabic index  
    if os.path.exists(arabic_index_path):
        try:
            arabic_index = faiss.read_index(arabic_index_path)
            arabic_actual_dim = arabic_index.d
            print(f"\n🇸🇦 Arabic FAISS Index Dimensions: {arabic_actual_dim}")
            print(f"🎯 Expected Arabic Dimensions: {expected_dims['arabic']}")
            arabic_dim_match = arabic_actual_dim == expected_dims['arabic']
            print(f"✅ Arabic Dimension Match: {arabic_dim_match}")
        except Exception as e:
            print(f"❌ Error loading Arabic index: {e}")
            arabic_dim_match = False
    else:
        print(f"❌ Arabic index not found: {arabic_index_path}")
        arabic_dim_match = False
        
    return french_dim_match and arabic_dim_match

def main():
    """Run complete embedding alignment verification."""
    
    print("🔧 Critical Fix #1: Embedding Alignment Verification")
    print("   Ensuring no garbage retrieval causes Chinese hallucination\n")
    
    # Change to backend directory
    os.chdir('/media/maria/DATA/4th year/sem1/NLP/project/git/Algerian-Law-RAG-Project/backend')
    
    # Check model alignment
    models_aligned = check_embedding_alignment()
    
    # Check dimension compatibility 
    dims_aligned = check_faiss_dimensions()
    
    print("\n" + "=" * 60)
    print("🏁 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if models_aligned and dims_aligned:
        print("🎉 ALL CHECKS PASSED!")
        print("   ✅ Embedding models match notebook configuration")
        print("   ✅ FAISS index dimensions match expected values")
        print("   🚀 Ready for generation config refactoring (Fix #2)")
        return True
    else:
        print("❌ VERIFICATION FAILED!")
        if not models_aligned:
            print("   🔧 Fix: Update backend settings to match notebook models")
        if not dims_aligned:
            print("   🔧 Fix: Regenerate FAISS indices with correct embedding models")
        print("   ⚠️  Current setup may cause garbage retrieval and hallucination")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)