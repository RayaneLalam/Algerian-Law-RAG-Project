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
    Supports Vector Search (default) and BM25 Search (Arabic only).
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
        self.arabic_bm25 = None  # New BM25 attribute
        
        # Track initialization
        self.french_ready = False
        self.arabic_ready = False
        self.arabic_bm25_ready = False
        
        # Load on initialization
        self._initialize_embedders()
        self._load_indices()
    
    def _initialize_embedders(self):
        """Initialize embedding models from cache (no downloading)."""
        # Use CPU for embeddings to avoid CUDA compatibility issues
        # while keeping CUDA available for LLM inference
        embedding_device = 'cpu'
        
        try:
            logger.info(f"Initializing embedding models on {embedding_device}...")
            # Load French embedder
            try:
                self.french_embedder = SentenceTransformer(self.settings.FRENCH_EMBEDDING_MODEL, local_files_only=True, device=embedding_device)
                logger.info(f"✓ French embedder loaded: {self.settings.FRENCH_EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load French embedder: {e}")
                self.french_embedder = None

            # Load Arabic embedder
            try:
                self.arabic_embedder = SentenceTransformer(self.settings.ARABIC_EMBEDDING_MODEL, local_files_only=True, device=embedding_device)
                logger.info(f"✓ Arabic embedder loaded: {self.settings.ARABIC_EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load Arabic embedder: {e}")
                self.arabic_embedder = None

            # Multilingual fallback
            self.multilingual_embedder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', local_files_only=True, device=embedding_device)
        except Exception as e:
            logger.error(f"Embedder initialization error: {e}")

    def _load_indices(self):
        """Load FAISS indices, document collections, and BM25."""
        self._load_french_index()
        self._load_arabic_index()
        self._load_arabic_bm25()

    def _load_french_index(self):
        """Load French FAISS index and documents."""
        try:
            if not os.path.exists(self.settings.FRENCH_INDEX_PATH):
                return
            self.french_index = faiss.read_index(self.settings.FRENCH_INDEX_PATH)
            with open(self.settings.FRENCH_DOCS_PATH, 'r', encoding='utf-8') as f:
                self.french_docs = json.load(f)
            self.french_ready = True
            logger.info(f"French index loaded: {len(self.french_docs)} documents")
        except Exception as e:
            logger.error(f"Failed to load French index: {e}")

    def _load_arabic_index(self):
        """Load Arabic FAISS index and documents."""
        try:
            if not os.path.exists(self.settings.ARABIC_INDEX_PATH):
                return
            self.arabic_index = faiss.read_index(self.settings.ARABIC_INDEX_PATH)
            with open(self.settings.ARABIC_META_PATH, 'rb') as f:
                arabic_meta = pickle.load(f)
            self.arabic_docs = arabic_meta.get('chunks', [])
            self.arabic_ready = True
            logger.info(f"Arabic Vector index loaded: {len(self.arabic_docs)} documents")
        except Exception as e:
            logger.error(f"Failed to load Arabic vector index: {e}")

    def _load_arabic_bm25(self):
        """Load Arabic BM25 index from pkl."""
        try:
            if os.path.exists(self.settings.ARABIC_BM25_PATH):
                with open(self.settings.ARABIC_BM25_PATH, 'rb') as f:
                    self.arabic_bm25 = pickle.load(f)
                self.arabic_bm25_ready = True
                logger.info("✓ Arabic BM25 index loaded successfully")
            else:
                logger.warning(f"Arabic BM25 path not found: {getattr(self.settings, 'ARABIC_BM25_PATH', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to load Arabic BM25: {e}")

    def search(
        self,
        query: str,
        language: str = 'fr',
        top_k: int = 3,
        search_type: str = 'embeddings'  # New parameter
    ) -> List[Dict]:
        """
        Search documents in specified language.
        
        Args:
            query: Search query
            language: 'fr' or 'ar'
            top_k: Number of results
            search_type: 'embeddings' (default) or 'bm25' (Arabic only)
        """
        language = self._normalize_language(language)
        results = []
        
        if language == 'ar':
            # Toggle between BM25 and Embeddings for Arabic
            if search_type == 'bm25' and self.arabic_bm25_ready:
                logger.info("Using Arabic BM25 search")
                results = self._search_arabic_bm25(query, top_k)
            elif self.arabic_ready:
                logger.info("Using Arabic Vector search")
                results = self._search_arabic(query, top_k)
            else:
                logger.warning("Arabic index not available, using multilingual fallback")
                results = self._search_multilingual(query, top_k, 'ar')
        else:
            # French only supports embeddings
            if self.french_ready:
                results = self._search_french(query, top_k)
            else:
                results = self._search_multilingual(query, top_k, 'fr')
        
        return results
    
    def _search_french(self, query: str, top_k: int) -> List[Dict]:
        """Search French index."""   
        try:
            if self.french_embedder is None:
                logger.error("French embedder not available")
                return []
       
            logger.debug(f"French search - total docs: {len(self.french_docs)}, index vectors: {self.french_index.ntotal}")

           
            query_embedding = self.french_embedder.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
       
            distances, indices = self.french_index.search(query_embedding.astype('float32'), top_k)

            logger.debug(f"FAISS returned {len(indices[0])} indices: {indices[0]}, distances: {distances[0]}")
           
            results = []
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx == -1:
                    logger.debug(f"Skipping invalid index: {idx}")
                    continue                
                logger.debug(f"Processing result {i}: doc_id={idx}, distance={distance}")             
                # Try to get document with robust ID lookup
                doc = None
         
                # Try integer index lookup
                try:
                    if isinstance(idx, (int, np.integer)) and 0 <= int(idx) < len(self.french_docs):

                        doc = self.french_docs[int(idx)]

                        logger.debug(f"Found doc at index {idx} (int lookup)")

                    else:

                        logger.warning(f"Index {idx} out of range [0, {len(self.french_docs)-1}]")

                        continue

                except (IndexError, TypeError) as e:

                    logger.warning(f"Doc ID {idx} not found in french docs: {e}")

                    continue

               

                if doc is None:

                    logger.warning(f"Doc ID {idx} not found in french docstore")

                    continue

               

                # Convert distance to similarity score based on FAISS metric

                # FAISS typically uses L2 distance or Inner Product

                # For L2: lower distance = higher similarity

                # For Inner Product with normalized vectors: higher score = higher similarity

                if distance < 0:  

                    # Inner product case - score is already similarity-like

                    similarity = abs(float(distance))

                elif distance <= 1.0:

                    # Likely inner product or cosine similarity (0-1 range)

                    similarity = 1.0 - float(distance)

                else:

                    # L2 distance case - convert to similarity

                    similarity = 1.0 / (1.0 + float(distance))

               

                result_doc = doc.copy()

                result_doc['score'] = float(distance)

                result_doc['similarity'] = similarity

                result_doc['language'] = 'fr'

                results.append(result_doc)

               

                logger.debug(f"Added result: similarity={similarity:.4f}, content_length={len(str(doc.get('content', '')))}")

           

            logger.info(f"French search returned {len(results)} results for query: {query[:50]}...")

            return results

           

        except Exception as e:

            logger.error(f"Error searching French index: {e}", exc_info=True)

            return []

   
    def _search_arabic_bm25(self, query: str, top_k: int) -> List[Dict]:
        try:
            # 1. Tokenize query (using the same logic as generation)
            tokenized_query = query.lower().split()
            
            # 2. Extract the actual BM25Okapi object from the dictionary
            # Since you saved it as {"bm25": bm25, ...}, we access it here:
            bm25_model = self.arabic_bm25["bm25"]
            
            # 3. Get scores
            scores = bm25_model.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score <= 0:
                    continue
                
                # Use the index to pull from your loaded docs
                if 0 <= idx < len(self.arabic_docs):
                    raw_doc = self.arabic_docs[idx]
                    doc = self._map_arabic_doc(raw_doc)
                    
                    result_doc = doc.copy()
                    result_doc['score'] = float(score)
                    # BM25 scores aren't 0-1. This is a rough normalization for the UI
                    result_doc['similarity'] = min(1.0, float(score) / 20.0) 
                    result_doc['language'] = 'ar'
                    result_doc['search_method'] = 'bm25'
                    results.append(result_doc)
            return results
        except Exception as e:
            logger.error(f"Error in Arabic BM25 search: {e}", exc_info=True)
            return []
        

    def _normalize_language(self, language: str) -> str:
        language = language.lower().strip()
        return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'

    def _map_arabic_doc(self, doc: Dict) -> Dict:
        mapped = doc.copy()
        if 'texte' in doc: mapped['content'] = doc['texte']
        if 'source' in doc: mapped['article'] = doc['source']
        elif 'titre' in doc: mapped['article'] = doc['titre']
        return mapped

    # ... (Rest of the original _search_french, _search_arabic, _search_multilingual methods)
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
            
            distances, indices = self.arabic_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1: continue
                
                try:
                    if 0 <= int(idx) < len(self.arabic_docs):
                        raw_doc = self.arabic_docs[int(idx)]
                        
                        # --- MODIFICATION START ---
                        # Map Arabic keys to standard keys
                        doc = self._map_arabic_doc(raw_doc)
                        # --- MODIFICATION END ---
                        
                        # Calculate similarity
                        if distance < 0: similarity = abs(float(distance))
                        elif distance <= 1.0: similarity = 1.0 - float(distance)
                        else: similarity = 1.0 / (1.0 + float(distance))
                        
                        result_doc = doc.copy()
                        result_doc['score'] = float(distance)
                        result_doc['similarity'] = similarity
                        result_doc['language'] = 'ar'
                        results.append(result_doc)
                except Exception as e:
                    logger.warning(f"Error processing Arabic doc {idx}: {e}")
                    continue
            
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
            
            logger.debug(f"Multilingual {language} search - total docs: {len(docs)}, index vectors: {index.ntotal}")
            
            distances, indices = index.search(query_embedding.astype('float32'), top_k)
            logger.debug(f"FAISS returned {len(indices[0])} indices: {indices[0]}, distances: {distances[0]}")
            
            results = []
            for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
                if idx == -1:
                    logger.debug(f"Skipping invalid index: {idx}")
                    continue
                    
                logger.debug(f"Processing result {i}: doc_id={idx}, distance={distance}")
                
                # Try to get document with robust ID lookup
                doc = None
                
                # Try integer index lookup
                try:
                    if isinstance(idx, (int, np.integer)) and 0 <= int(idx) < len(docs):
                        doc = docs[int(idx)]
                        logger.debug(f"Found doc at index {idx} (int lookup)")
                    else:
                        logger.warning(f"Index {idx} out of range [0, {len(docs)-1}]")
                        continue
                except (IndexError, TypeError) as e:
                    logger.warning(f"Doc ID {idx} not found in {language} docs: {e}")
                    continue
                
                if doc is None:
                    logger.warning(f"Doc ID {idx} not found in {language} docstore")
                    continue
                
                # Convert distance to similarity score based on FAISS metric
                # FAISS typically uses L2 distance or Inner Product
                # For L2: lower distance = higher similarity
                # For Inner Product with normalized vectors: higher score = higher similarity
                if distance < 0:  
                    # Inner product case - score is already similarity-like
                    similarity = abs(float(distance))
                elif distance <= 1.0:
                    # Likely inner product or cosine similarity (0-1 range)
                    similarity = 1.0 - float(distance)
                else:
                    # L2 distance case - convert to similarity
                    similarity = 1.0 / (1.0 + float(distance))
                
                result_doc = doc.copy()
                result_doc['score'] = float(distance)
                result_doc['similarity'] = similarity
                result_doc['language'] = language
                results.append(result_doc)
                
                logger.debug(f"Added result: similarity={similarity:.4f}, content_length={len(str(doc.get('content', '')))}")
            
            logger.info(f"Multilingual search returned {len(results)} results for {language} query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in multilingual search: {e}", exc_info=True)
            return []

    def test_search_debug(self, query: str = "constitution", language: str = "fr") -> Dict:
        """Debug method to test search functionality and return diagnostic info."""
        logger.info(f"=== DEBUG SEARCH TEST ===")
        logger.info(f"Query: {query}, Language: {language}")
        
        debug_info = {
            "query": query,
            "language": language,
            "service_status": {
                "french_ready": self.french_ready,
                "arabic_ready": self.arabic_ready,
                "french_embedder": self.french_embedder is not None,
                "arabic_embedder": self.arabic_embedder is not None,
                "multilingual_embedder": self.multilingual_embedder is not None
            },
            "data_status": {
                "french_docs_count": len(self.french_docs) if self.french_docs else 0,
                "arabic_docs_count": len(self.arabic_docs) if self.arabic_docs else 0,
                "french_index_vectors": self.french_index.ntotal if self.french_index else 0,
                "arabic_index_vectors": self.arabic_index.ntotal if self.arabic_index else 0
            },
            "search_results": []
        }
        
        # Perform search
        try:
            results = self.search(query, language, top_k=3)
            debug_info["search_results"] = results
            debug_info["results_count"] = len(results)
            
            logger.info(f"DEBUG: Found {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"Result {i+1}: similarity={result.get('similarity', 0):.4f}, content_length={len(str(result.get('content', '')))}")
                
        except Exception as e:
            debug_info["error"] = str(e)
            logger.error(f"DEBUG: Search failed: {e}", exc_info=True)
        
        return debug_info
