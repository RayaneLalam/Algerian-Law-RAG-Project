import json
import logging
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

# Clear GPU cache to avoid OOM errors
try:
    import torch
    torch.cuda.empty_cache()
except:
    pass

logger = logging.getLogger(__name__)


class BilingualSearchService:
    """
    Bilingual search service with separate French and Arabic indices.
    
    Routes queries to appropriate language-specific index and embedder.
    Handles fallback to multilingual embedder if language-specific index unavailable.
    """
    
    def __init__(self):
        from app.config.settings import settings
        
        self.settings = settings
        
        # Initialize language-specific embedders
        self.french_embedder = None
        self.arabic_embedder = None
        self.multilingual_embedder = None
        
        # Initialize indices
        self.french_index = None
        self.french_docs = None
        self.arabic_index = None
        self.arabic_docs = None
        
        # Track initialization
        self.french_ready = False
        self.arabic_ready = False
        
        # Load on initialization
        self._initialize_embedders()
        self._load_indices()
    
    def _initialize_embedders(self):
        """Initialize embedding models from cache (no downloading)."""
        # Get compute device from environment
        device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
        if device not in ['cuda', 'cpu']:
            device = 'cuda'
        
        try:
            import torch
            if device == 'cuda':
                torch.cuda.empty_cache()
        except:
            pass
            
        try:
            logger.info(f"Initializing embedding models on {device}...")
            # Load French embedder (CamemBERT - 1024 dims - matches FAISS index)
            try:
                self.french_embedder = SentenceTransformer(self.settings.FRENCH_EMBEDDING_MODEL, local_files_only=True, device=device)
                logger.info(f"✓ French embedder loaded on {device}: {self.settings.FRENCH_EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load French embedder: {e}")
                logger.warning("French embedder not available - search will use fallback")
                self.french_embedder = None
        except Exception as e:
            logger.error(f"French embedder initialization error: {e}")
            self.french_embedder = None
        
        try:
            try:
                import torch
                if device == 'cuda':
                    torch.cuda.empty_cache()
            except:
                pass
            # Load Arabic embedder (Multilingual - 384 dims)
            try:
                self.arabic_embedder = SentenceTransformer(self.settings.ARABIC_EMBEDDING_MODEL, local_files_only=True, device=device)
                logger.info(f"✓ Arabic embedder loaded on {device}: {self.settings.ARABIC_EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load Arabic embedder: {e}")
                logger.warning("Arabic embedder not available - search will use fallback")
                self.arabic_embedder = None
        except Exception as e:
            logger.error(f"Arabic embedder initialization error: {e}")
            self.arabic_embedder = None
        
        # Multilingual fallback (always load from cache)
        try:
            try:
                import torch
                if device == 'cuda':
                    torch.cuda.empty_cache()
            except:
                pass
            self.multilingual_embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', local_files_only=True, device=device)
            logger.info(f"✓ Multilingual embedder loaded on {device} as fallback")
        except Exception as e:
            logger.error(f"Failed to load multilingual embedder from cache: {e}")
            self.multilingual_embedder = None
    
    def _load_indices(self):
        """Load FAISS indices and document collections."""
        self._load_french_index()
        self._load_arabic_index()
    
    def _load_french_index(self):
        """Load French FAISS index and documents."""
        try:
            if not os.path.exists(self.settings.FRENCH_INDEX_PATH):
                logger.warning(f"French index not found at {self.settings.FRENCH_INDEX_PATH}")
                self.french_ready = False
                return
            
            self.french_index = faiss.read_index(self.settings.FRENCH_INDEX_PATH)
            
            if not os.path.exists(self.settings.FRENCH_DOCS_PATH):
                logger.warning(f"French docs not found at {self.settings.FRENCH_DOCS_PATH}")
                self.french_index = None
                self.french_ready = False
                return
            
            with open(self.settings.FRENCH_DOCS_PATH, 'r', encoding='utf-8') as f:
                self.french_docs = json.load(f)
            
            logger.info(f"French index loaded: {self.french_index.ntotal} vectors, {len(self.french_docs)} documents")
            self.french_ready = True
            
        except Exception as e:
            logger.error(f"Failed to load French index: {e}", exc_info=True)
            self.french_index = None
            self.french_docs = None
            self.french_ready = False
    
    def _load_arabic_index(self):
        """Load Arabic FAISS index and documents."""
        try:
            if not os.path.exists(self.settings.ARABIC_INDEX_PATH):
                logger.warning(f"Arabic index not found at {self.settings.ARABIC_INDEX_PATH}")
                self.arabic_ready = False
                return
            
            self.arabic_index = faiss.read_index(self.settings.ARABIC_INDEX_PATH)
            
            if not os.path.exists(self.settings.ARABIC_META_PATH):
                logger.warning(f"Arabic metadata not found at {self.settings.ARABIC_META_PATH}")
                self.arabic_index = None
                self.arabic_ready = False
                return
            
            with open(self.settings.ARABIC_META_PATH, 'rb') as f:
                arabic_meta = pickle.load(f)
            
            self.arabic_docs = arabic_meta.get('chunks', [])
            
            logger.info(f"Arabic index loaded: {self.arabic_index.ntotal} vectors, {len(self.arabic_docs)} documents")
            self.arabic_ready = True
            
        except Exception as e:
            logger.error(f"Failed to load Arabic index: {e}", exc_info=True)
            self.arabic_index = None
            self.arabic_docs = None
            self.arabic_ready = False
    
    def search(
        self,
        query: str,
        language: str = 'fr',
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search documents in specified language.
        
        Args:
            query: Search query
            language: 'fr' or 'ar'
            top_k: Number of results
            
        Returns:
            List of documents with scores and language metadata
        """
        language = self._normalize_language(language)
        
        if language == 'ar':
            if self.arabic_ready:
                return self._search_arabic(query, top_k)
            else:
                logger.warning("Arabic index not available, using multilingual embedder")
                return self._search_multilingual(query, top_k, 'ar')
        else:
            if self.french_ready:
                return self._search_french(query, top_k)
            else:
                logger.warning("French index not available, using multilingual embedder")
                return self._search_multilingual(query, top_k, 'fr')
    
    def _normalize_language(self, language: str) -> str:
        """Normalize language code."""
        language = language.lower().strip()
        return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'
    
    def _search_french(self, query: str, top_k: int) -> List[Dict]:
        """Search French index."""
        try:
            if self.french_embedder is None:
                logger.error("French embedder not available")
                return []
            
            query_embedding = self.french_embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            scores, indices = self.french_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if 0 <= idx < len(self.french_docs) and idx != -1:
                    doc = self.french_docs[idx].copy()
                    doc['score'] = float(score)
                    doc['language'] = 'fr'
                    results.append(doc)
            
            logger.debug(f"French search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching French index: {e}", exc_info=True)
            return []
    
    def _search_arabic(self, query: str, top_k: int) -> List[Dict]:
        """Search Arabic index."""
        try:
            if self.arabic_embedder is None:
                logger.error("Arabic embedder not available")
                return []
            
            query_embedding = self.arabic_embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            scores, indices = self.arabic_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if 0 <= idx < len(self.arabic_docs) and idx != -1:
                    doc = self.arabic_docs[idx].copy()
                    doc['score'] = float(score)
                    doc['language'] = 'ar'
                    results.append(doc)
            
            logger.debug(f"Arabic search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching Arabic index: {e}", exc_info=True)
            return []
    
    def _search_multilingual(self, query: str, top_k: int, language: str) -> List[Dict]:
        """Fallback multilingual search."""
        try:
            if self.multilingual_embedder is None:
                logger.error("Multilingual embedder not available")
                return []
            
            query_embedding = self.multilingual_embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            if language == 'ar' and self.arabic_index:
                index = self.arabic_index
                docs = self.arabic_docs
            elif language == 'fr' and self.french_index:
                index = self.french_index
                docs = self.french_docs
            else:
                logger.warning(f"No index available for multilingual fallback")
                return []
            
            scores, indices = index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if 0 <= idx < len(docs) and idx != -1:
                    doc = docs[idx].copy()
                    doc['score'] = float(score)
                    doc['language'] = language
                    results.append(doc)
            
            logger.debug(f"Multilingual search returned {len(results)} results for {language}")
            return results
            
        except Exception as e:
            logger.error(f"Error in multilingual search: {e}", exc_info=True)
            return []
