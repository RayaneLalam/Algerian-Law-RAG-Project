import json
import logging
import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict

from .utils import normalize_language, reciprocal_rank_fusion
from .engines import SearchEnginesMixin

# Clear GPU cache
try:
    import torch
    torch.cuda.empty_cache()
except:
    pass

logger = logging.getLogger(__name__)

class BilingualSearchService(SearchEnginesMixin):
    def __init__(self):
        from app.config.settings import settings
        self.settings = settings
        
        self.french_embedder = None
        self.arabic_embedder = None
        self.multilingual_embedder = None
        
        self.french_index = None
        self.french_docs = None
        self.french_bm25 = None
        self.arabic_index = None
        self.arabic_docs = None
        self.arabic_bm25 = None
        
        self.french_ready = False
        self.french_bm25_ready = False
        self.arabic_ready = False
        self.arabic_bm25_ready = False
        
        self._initialize_embedders()
        self._load_indices()

    def _initialize_embedders(self):
        device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
        if device not in ['cuda', 'cpu']: device = 'cuda'
        
        try:
            logger.info(f"Initializing embedding models on {device}...")
            try:
                self.french_embedder = SentenceTransformer(self.settings.FRENCH_EMBEDDING_MODEL, local_files_only=True, device=device)
            except Exception as e: logger.error(f"Failed French embedder: {e}")
            
            try:
                self.arabic_embedder = SentenceTransformer(self.settings.ARABIC_EMBEDDING_MODEL, local_files_only=True, device=device)
            except Exception as e: logger.error(f"Failed Arabic embedder: {e}")
            
            self.multilingual_embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', local_files_only=True, device=device)
        except Exception as e:
            logger.error(f"Embedder initialization error: {e}")

    def _load_indices(self):
        self._load_french_index()
        self._load_french_bm25()
        self._load_arabic_index()
        self._load_arabic_bm25()

    def _load_french_index(self):
        try:
            if not os.path.exists(self.settings.FRENCH_INDEX_PATH): return
            self.french_index = faiss.read_index(self.settings.FRENCH_INDEX_PATH)
            with open(self.settings.FRENCH_DOCS_PATH, 'r', encoding='utf-8') as f:
                self.french_docs = json.load(f)
            self.french_ready = True
        except Exception as e: logger.error(f"Failed French index: {e}")

    def _load_french_bm25(self):
        try:
            if os.path.exists(self.settings.FRENCH_BM25_PATH):
                with open(self.settings.FRENCH_BM25_PATH, 'rb') as f:
                    self.french_bm25 = pickle.load(f)
                self.french_bm25_ready = True
        except Exception as e: logger.error(f"Failed French BM25: {e}")

    def _load_arabic_index(self):
        try:
            if not os.path.exists(self.settings.ARABIC_INDEX_PATH): return
            self.arabic_index = faiss.read_index(self.settings.ARABIC_INDEX_PATH)
            with open(self.settings.ARABIC_META_PATH, 'rb') as f:
                arabic_meta = pickle.load(f)
            self.arabic_docs = arabic_meta.get('chunks', [])
            self.arabic_ready = True
        except Exception as e: logger.error(f"Failed Arabic index: {e}")

    def _load_arabic_bm25(self):
        try:
            if os.path.exists(self.settings.ARABIC_BM25_PATH):
                with open(self.settings.ARABIC_BM25_PATH, 'rb') as f:
                    self.arabic_bm25 = pickle.load(f)
                self.arabic_bm25_ready = True
        except Exception as e: logger.error(f"Failed Arabic BM25: {e}")

    def search(self, query: str, language: str = 'fr', top_k: int = 3, search_type: str = 'embeddings') -> List[Dict]:
        language = normalize_language(language)
        if language == 'ar':
            if search_type == 'bm25' and self.arabic_bm25_ready: return self._search_arabic_bm25(query, top_k)
            if self.arabic_ready: return self._search_arabic(query, top_k)
            return self._search_multilingual(query, top_k, 'ar')
        else:
            if search_type == 'bm25' and self.french_bm25_ready: return self._search_french_bm25(query, top_k)
            if self.french_ready: return self._search_french(query, top_k)
            return self._search_multilingual(query, top_k, 'fr')

    def test_search_debug(self, query: str = "constitution", language: str = "fr") -> Dict:
        # Diagnostic code (logic remains identical to original)
        results = self.search(query, language, top_k=3)
        return {"query": query, "results_count": len(results), "search_results": results}
    

    def hybrid_search(self, query: str, language: str = 'fr', top_k: int = 3) -> List[Dict]:
        """
        Performs hybrid search by retrieving 15 results from BM25 and 
        15 from Vector search, then merging the top 3.
        """
        language = normalize_language(language)
        
        # 1. Retrieve 15 from each engine
        # We call the internal methods directly
        if language == 'ar':
            vector_results = self._search_arabic(query, top_k=15)
            bm25_results = self._search_arabic_bm25(query, top_k=15)
        else:
            vector_results = self._search_french(query, top_k=15)
            bm25_results = self._search_french_bm25(query, top_k=15)

        # 2. Merge using RRF
        merged_results = reciprocal_rank_fusion([vector_results, bm25_results])

        # 3. Return the best 3
        return merged_results[:top_k]