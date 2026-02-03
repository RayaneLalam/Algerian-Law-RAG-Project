import json
import logging
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Use os.path.join for cross-platform compatibility
BASE_DIR = "data/faiss"
# The filename indicates this index was built with dangvantuan-sentence-camembert-large
MODEL_NAME_USED_FOR_INDEX = "dangvantuan-sentence-camembert-large"
FILE_PREFIX = "algerian_legal(jo+constitution+penale+civil+commerce+famille) embedder_ dangvantuan-sentence-camembert-large"

FAISS_INDEX_PATH = os.path.join(BASE_DIR, f"{FILE_PREFIX}.faiss")
DOCS_JSON_PATH = os.path.join(BASE_DIR, f"{FILE_PREFIX}_docs.json")
META_JSON_PATH = os.path.join(BASE_DIR, f"{FILE_PREFIX}_meta.json")

TOP_N_RESULTS = 3

class SearchService:
    """
    Search service for Algerian legal documents using pre-built FAISS index.
    """

    def __init__(self, embedding_model: str = None):
        # 1. FIX: Ensure the model matches the one used to create the index
        self.embedding_model_name = embedding_model or f"dangvantuan/{MODEL_NAME_USED_FOR_INDEX}"
        
        # 2. FIX: Ensure the directory exists correctly
        if not os.path.exists(BASE_DIR):
            os.makedirs(BASE_DIR, exist_ok=True)
            logger.info(f"Created directory: {BASE_DIR}")

        # Get compute device
        self.device = os.getenv('COMPUTE_DEVICE', 'cuda').lower()
        if self.device == 'cuda':
            try:
                import torch
                if not torch.cuda.is_available():
                    self.device = 'cpu'
            except ImportError:
                self.device = 'cpu'
        
        self.model = None
        self.documents = []
        self.metadata = {}
        self.vector_index = None
        self.is_fitted = False

        # Load on init
        self.load_data()

    def _load_embedding_model(self):
        """Lazily load the embedding model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            try:
                # Try local first, then download
                self.model = SentenceTransformer(self.embedding_model_name, device=self.device)
            except Exception as e:
                logger.error(f"Failed to load model {self.embedding_model_name}: {e}")
                raise

    def load_data(self):
        """Load documents, metadata, and FAISS index from pre-built files."""
        try:
            # Check for file existence
            paths = [FAISS_INDEX_PATH, DOCS_JSON_PATH, META_JSON_PATH]
            for p in paths:
                if not os.path.exists(p):
                    logger.error(f"Missing required file: {p}")
                    return False

            # Load documents
            with open(DOCS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)

            # Load metadata
            with open(META_JSON_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

            # Load FAISS index
            self.vector_index = faiss.read_index(FAISS_INDEX_PATH)
            
            # 3. FIX: Consistency Check
            if self.vector_index.ntotal != len(self.documents):
                logger.warning(f"Index size ({self.vector_index.ntotal}) != Doc count ({len(self.documents)})")

            self.is_fitted = True
            logger.info("SearchService initialized successfully.")
            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            return False

    def search(self, query: str, top_n: int = TOP_N_RESULTS):
        if not self.is_fitted:
            logger.error("SearchService not properly initialized.")
            return []

        self._load_embedding_model()

        # Encode query
        q_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')

        # Search
        k = min(top_n, self.vector_index.ntotal)
        scores, indices = self.vector_index.search(q_emb, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(self.documents):
                continue

            results.append({
                "index": int(idx),
                "score": float(scores[0][i]),
                "document": self.documents[idx]
            })
        return results