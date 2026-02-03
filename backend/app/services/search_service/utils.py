import logging
from typing import Dict

logger = logging.getLogger(__name__)

def normalize_language(language: str) -> str:
    language = language.lower().strip()
    return 'ar' if language in ('ar', 'arabic', 'العربية') else 'fr'

def map_arabic_doc(doc: Dict) -> Dict:
    mapped = doc.copy()
    if 'texte' in doc: mapped['content'] = doc['texte']
    if 'source' in doc: mapped['article'] = doc['source']
    elif 'titre' in doc: mapped['article'] = doc['titre']
    return mapped


def reciprocal_rank_fusion(search_results_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """
    Standard RRF algorithm to merge multiple ranked result lists.
    k is a smoothing factor (default 60 is standard).
    """
    fused_scores = {}
    # Map to store the actual document content for the final list
    doc_map = {}

    for results in search_results_lists:
        for rank, doc in enumerate(results):
            # We need a unique identifier for the document. 
            # Using content hash or a specific ID field if available.
            doc_id = doc.get('id') or hash(doc.get('content', ''))
            
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0.0
                doc_map[doc_id] = doc
            
            # RRF Formula: 1 / (k + rank)
            fused_scores[doc_id] += 1.0 / (k + rank + 1)

    # Sort by the new fused score
    reranked_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    
    final_results = []
    for doc_id, score in reranked_ids:
        final_doc = doc_map[doc_id].copy()
        final_doc['hybrid_score'] = score
        final_results.append(final_doc)
        
    return final_results