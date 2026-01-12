import json
import logging
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Clear GPU cache to avoid OOM errors
try:
    import torch
    torch.cuda.empty_cache()
except:
    pass
#from src.config.settings import DATA_PATH, VECTOR_DB_PATH, TOP_N_RESULTS
DATA_PATH = "data/laws.json"
VECTOR_DB_PATH = "data/laws.index"
TOP_N_RESULTS = 3
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchService:
    """
    Search service for Algerian legal documents using pre-built FAISS index.
    Loads existing index created by the notebook.
    """

    def __init__(self,
                 embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        # Ensure data dirs exist
        data_dir = os.path.dirname(DATA_PATH) or "."
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        vector_db_dir = os.path.dirname(VECTOR_DB_PATH) or "."
        if not os.path.exists(vector_db_dir):
            os.makedirs(vector_db_dir, exist_ok=True)

        # Get compute device from environment
        device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
        if device not in ['cuda', 'cpu']:
            device = 'cuda'
        
        # Model and storage
        self.embedding_model_name = embedding_model
        # Load model from cache only (no downloading)
        try:
            self.model = SentenceTransformer(self.embedding_model_name, local_files_only=True, device=device)
        except (OSError, ValueError):
            # If cache is empty, download once
            logger.warning(f"Model not in cache, downloading: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name, device=device)

        # In-memory state
        self.documents = []             # List of all document chunks
        self.metadata = {}              # Index metadata
        self.vector_index = None        # faiss index
        self.is_fitted = False

        # Load on init
        self.load_data()

    def _load_embedding_model(self):
        """Lazily load the embedding model (only when needed for new queries)"""
        if self.model is None:
            logger.info(
                f"Loading embedding model: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")

    def load_data(self):
        """Load documents, metadata, and FAISS index from pre-built files."""
        try:
            # Check if all required files exist
            if not os.path.exists(FAISS_INDEX_PATH):
                logger.error(f"FAISS index not found at: {FAISS_INDEX_PATH}")
                return False

            if not os.path.exists(DOCS_JSON_PATH):
                logger.error(f"Documents JSON not found at: {DOCS_JSON_PATH}")
                return False

            if not os.path.exists(META_JSON_PATH):
                logger.error(f"Metadata JSON not found at: {META_JSON_PATH}")
                return False

            # Load documents
            logger.info(f"Loading documents from {DOCS_JSON_PATH}")
            with open(DOCS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            logger.info(f"Loaded {len(self.documents)} documents")

            # Load metadata
            logger.info(f"Loading metadata from {META_JSON_PATH}")
            with open(META_JSON_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info(f"Metadata: {self.metadata}")

            # Load FAISS index
            logger.info(f"Loading FAISS index from {FAISS_INDEX_PATH}")
            self.vector_index = faiss.read_index(FAISS_INDEX_PATH)
            logger.info(
                f"FAISS index loaded successfully with {self.vector_index.ntotal} vectors")

            # Verify consistency
            if self.vector_index.ntotal != len(self.documents):
                logger.warning(
                    f"Index size ({self.vector_index.ntotal}) doesn't match "
                    f"document count ({len(self.documents)}). This may cause issues."
                )

            self.is_fitted = True
            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            self.documents = []
            self.vector_index = None
            self.is_fitted = False
            return False

    def _vector_search(self, query, top_n=TOP_N_RESULTS):
        """Return top_n matches for the query"""
        if self.vector_index is None or self.vector_index.ntotal == 0:
            logger.warning("Vector index is not initialized or empty.")
            return []

        # Load model if not already loaded
        self._load_embedding_model()

        # Encode query
        logger.debug(f"Encoding query: {query[:100]}...")
        q_emb = self.model.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        q_emb = q_emb.astype('float32').reshape(1, -1)

        # Search (k cannot exceed ntotal)
        k = min(top_n, self.vector_index.ntotal)
        scores, indices = self.vector_index.search(q_emb, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue

            score = float(scores[0][i])
            # Inner product score is already similarity for normalized vectors
            similarity = score

            # Get document
            if idx < len(self.documents):
                doc = self.documents[idx]
            else:
                logger.warning(f"Index {idx} out of range for documents list")
                doc = {}

            result = {
                "index": int(idx),
                "score": score,
                "similarity": similarity,
                "document": doc
            }
            results.append(result)

        logger.debug(f"Found {len(results)} results")
        return results

    def search(self, query: str, top_n: int = TOP_N_RESULTS):
        """
        Public search method.
        Returns list of result dicts sorted by best similarity.
        """
        if not self.is_fitted:
            logger.error(
                "SearchService not properly initialized. Check if all files exist.")
            return []

        try:
            return self._vector_search(query, top_n=top_n)
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return []

    def format_search_results(self, results):
        """Return a human-friendly string list from results"""
        formatted = []
        for i, r in enumerate(results, start=1):
            doc = r.get("document", {})
            doc_type = doc.get("source_document_type", "").upper()
            header = doc.get("header", "Sans titre")
            sim = r.get("similarity", 0.0)
            content_preview = doc.get("content", "")[:150]
            formatted.append(
                f"{i}. [{sim:.4f}] [{doc_type}] {header}\n   {content_preview}..."
            )
        return formatted

    def get_stats(self):
        """Return statistics about the loaded data"""
        if not self.is_fitted:
            return {"status": "not_fitted"}

        doc_types = {}
        for doc in self.documents:
            doc_type = doc.get("source_document_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        return {
            "status": "ready",
            "total_documents": len(self.documents),
            "index_vectors": self.vector_index.ntotal if self.vector_index else 0,
            "embedding_model": self.embedding_model_name,
            "embedding_dimension": self.metadata.get("dimension", "unknown"),
            "document_types": doc_types
        }
