#!/usr/bin/env python3
"""
Embedding Dimension Verification Script
Checks alignment between notebook models and backend service models
"""

import os
import sys

def verify_embedding_dimensions():
    """Verify that embedding models have consistent dimensions"""
    
    print("🔍 EMBEDDING DIMENSION VERIFICATION")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Models from settings
        FRENCH_EMBEDDING_MODEL = 'dangvantuan/sentence-camembert-large'
        ARABIC_EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        
        print(f"French Model: {FRENCH_EMBEDDING_MODEL}")
        print(f"📋 Arabic Model: {ARABIC_EMBEDDING_MODEL}")
        print()
        
        # Load and check French embedding model
        print("🔄 Loading French embedding model...")
        try:
            french_embedder = SentenceTransformer(FRENCH_EMBEDDING_MODEL)
            french_dims = french_embedder.get_sentence_embedding_dimension()
            print(f"✅ French Model Dimensions: {french_dims}")
        except Exception as e:
            print(f"❌ Error loading French model: {e}")
            french_dims = None
        
        # Load and check Arabic embedding model
        print("\n🔄 Loading Arabic embedding model...")
        try:
            arabic_embedder = SentenceTransformer(ARABIC_EMBEDDING_MODEL)
            arabic_dims = arabic_embedder.get_sentence_embedding_dimension()
            print(f"✅ Arabic Model Dimensions: {arabic_dims}")
        except Exception as e:
            print(f"❌ Error loading Arabic model: {e}")
            arabic_dims = None
        
        print("\n" + "=" * 50)
        print("📊 DIMENSION SUMMARY")
        print("=" * 50)
        
        if french_dims:
            print(f"French (CamemBERT): {french_dims} dimensions")
            if french_dims == 1024:
                print("✅ French dimensions match expected CamemBERT-large (1024)")
            else:
                print(f"⚠️  French dimensions unexpected. Expected 1024, got {french_dims}")
        
        if arabic_dims:
            print(f"Arabic (Multilingual): {arabic_dims} dimensions")
            if arabic_dims == 384:
                print("✅ Arabic dimensions match expected MiniLM-L12-v2 (384)")
            else:
                print(f"⚠️  Arabic dimensions unexpected. Expected 384, got {arabic_dims}")
        
        # Check FAISS index compatibility
        print("\n🔍 FAISS INDEX COMPATIBILITY CHECK")
        print("-" * 30)
        
        # Check if FAISS indices exist and verify dimensions
        faiss_paths = {
            'french': './data/faiss/algerian_legal*camembert*.faiss',
            'arabic': './data/laws_ar.index'
        }
        
        try:
            import faiss
            import glob
            
            # Check French FAISS index
            french_files = glob.glob('./data/faiss/*camembert*.faiss')
            if french_files:
                french_index = faiss.read_index(french_files[0])
                faiss_french_dims = french_index.d
                print(f"📁 French FAISS Index Dimensions: {faiss_french_dims}")
                if french_dims and faiss_french_dims == french_dims:
                    print("✅ French embedding-FAISS dimension match!")
                else:
                    print(f"❌ MISMATCH: Embedding {french_dims} vs FAISS {faiss_french_dims}")
            else:
                print("⚠️  French FAISS index not found")
            
            # Check Arabic FAISS index  
            arabic_files = glob.glob('./data/laws_ar.index')
            if arabic_files:
                arabic_index = faiss.read_index(arabic_files[0])
                faiss_arabic_dims = arabic_index.d
                print(f"📁 Arabic FAISS Index Dimensions: {faiss_arabic_dims}")
                if arabic_dims and faiss_arabic_dims == arabic_dims:
                    print("✅ Arabic embedding-FAISS dimension match!")
                else:
                    print(f"❌ MISMATCH: Embedding {arabic_dims} vs FAISS {faiss_arabic_dims}")
            else:
                print("⚠️  Arabic FAISS index not found")
                
        except ImportError:
            print("⚠️  FAISS not available for index dimension check")
        except Exception as e:
            print(f"❌ Error checking FAISS indices: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 RECOMMENDATIONS")
        print("=" * 50)
        
        if french_dims == 1024 and arabic_dims == 384:
            print("✅ All embedding dimensions are correct!")
            print("✅ French: dangvantuan/sentence-camembert-large (1024D)")
            print("✅ Arabic: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384D)")
        else:
            print("❌ Dimension mismatches detected!")
            print("\n🔧 Required fixes:")
            if french_dims != 1024:
                print(f"   - Fix French model: Expected 1024D, got {french_dims}D")
            if arabic_dims != 384:
                print(f"   - Fix Arabic model: Expected 384D, got {arabic_dims}D")
            print("\n⚠️  Mismatched dimensions cause garbage retrieval and hallucination!")
        
        return french_dims == 1024 and arabic_dims == 384
        
    except Exception as e:
        print(f"❌ Critical error during verification: {e}")
        return False

if __name__ == "__main__":
    success = verify_embedding_dimensions()
    sys.exit(0 if success else 1)