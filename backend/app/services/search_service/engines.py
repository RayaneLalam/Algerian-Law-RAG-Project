import logging
import numpy as np
from typing import List, Dict
from .utils import map_arabic_doc

logger = logging.getLogger(__name__)

class SearchEnginesMixin:
    """Internal search implementations for the BilingualSearchService."""

    def _search_french_bm25(self, query: str, top_k: int) -> List[Dict]:
        try:
            tokenized_query = query.lower().split()
            bm25_model = self.french_bm25["bm25"]
            scores = bm25_model.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score <= 0: continue
                if 0 <= idx < len(self.french_docs):
                    doc = self.french_docs[idx]
                    result_doc = doc.copy()
                    result_doc.update({
                        'score': float(score),
                        'similarity': min(1.0, float(score) / 20.0),
                        'language': 'fr',
                        'search_method': 'bm25'
                    })
                    results.append(result_doc)
            return results
        except Exception as e:
            logger.error(f"Error in French BM25 search: {e}", exc_info=True)
            return []

    def _search_arabic_bm25(self, query: str, top_k: int) -> List[Dict]:
        try:
            tokenized_query = query.lower().split()
            bm25_model = self.arabic_bm25["bm25"]
            scores = bm25_model.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score <= 0: continue
                if 0 <= idx < len(self.arabic_docs):
                    doc = map_arabic_doc(self.arabic_docs[idx])
                    result_doc = doc.copy()
                    result_doc.update({
                        'score': float(score),
                        'similarity': min(1.0, float(score) / 20.0),
                        'language': 'ar',
                        'search_method': 'bm25'
                    })
                    results.append(result_doc)
            return results
        except Exception as e:
            logger.error(f"Error in Arabic BM25 search: {e}", exc_info=True)
            return []

    def _search_arabic(self, query: str, top_k: int) -> List[Dict]:
        try:
            if self.arabic_embedder is None: return []
            query_embedding = self.arabic_embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            distances, indices = self.arabic_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1: continue
                try:
                    if 0 <= int(idx) < len(self.arabic_docs):
                        doc = map_arabic_doc(self.arabic_docs[int(idx)])
                        similarity = abs(float(distance)) if distance < 0 else (1.0 - float(distance) if distance <= 1.0 else 1.0 / (1.0 + float(distance)))
                        result_doc = doc.copy()
                        result_doc.update({'score': float(distance), 'similarity': similarity, 'language': 'ar'})
                        results.append(result_doc)
                except Exception as e:
                    logger.warning(f"Error processing Arabic doc {idx}: {e}")
            return results
        except Exception as e:
            logger.error(f"Error searching Arabic index: {e}", exc_info=True)
            return []

    def _search_french(self, query: str, top_k: int) -> List[Dict]:
        try:
            if self.french_embedder is None: return []
            query_embedding = self.french_embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            distances, indices = self.french_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1 or not (0 <= int(idx) < len(self.french_docs)): continue
                doc = self.french_docs[int(idx)]
                similarity = abs(float(distance)) if distance < 0 else (1.0 - float(distance) if distance <= 1.0 else 1.0 / (1.0 + float(distance)))
                result_doc = doc.copy()
                result_doc.update({'score': float(distance), 'similarity': similarity, 'language': 'fr'})
                results.append(result_doc)
            return results
        except Exception as e:
            logger.error(f"Error searching French index: {e}", exc_info=True)
            return []

    def _search_multilingual(self, query: str, top_k: int, language: str) -> List[Dict]:
        try:
            if self.multilingual_embedder is None: return []
            query_embedding = self.multilingual_embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            index = self.arabic_index if language == 'ar' else self.french_index
            docs = self.arabic_docs if language == 'ar' else self.french_docs
            if not index: return []
            
            distances, indices = index.search(query_embedding.astype('float32'), top_k)
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1 or not (0 <= int(idx) < len(docs)): continue
                doc = docs[int(idx)]
                similarity = abs(float(distance)) if distance < 0 else (1.0 - float(distance) if distance <= 1.0 else 1.0 / (1.0 + float(distance)))
                result_doc = doc.copy()
                result_doc.update({'score': float(distance), 'similarity': similarity, 'language': language})
                results.append(result_doc)
            return results
        except Exception as e:
            logger.error(f"Error in multilingual search: {e}", exc_info=True)
            return []