import json
import logging
import os
import time
import numpy as np
import faiss
import pickle
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
    Simplified search service that uses only vector embeddings (sentence-transformers + FAISS).
    Expects DATA_PATH to be a JSON file containing a list of document dicts (e.g., laws).
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
        self.chunks = []                # list of dicts (documents)
        self.embedding_vectors = None   # numpy array (n_documents, dim)
        self.vector_index = None        # faiss index
        self.is_fitted = False

        # Load on init
        self.load_data()

    def _texts_from_chunks(self, chunks):
        """
        Convert a list of chunk dicts to the text strings to embed.
        Default behavior: combine 'titre' and 'texte' if present, otherwise str(chunk).
        """
        texts = []
        for c in chunks:
            if isinstance(c, dict):
                titre = c.get("titre", "")
                texte = c.get("texte", "")
                combined = f"{titre} - {texte}".strip()
                if not combined:
                    combined = json.dumps(c, ensure_ascii=False)
                texts.append(combined)
            else:
                texts.append(str(c))
        return texts

    def load_data(self):
        """Load document JSON and (if present) vector DB + metadata."""
        try:
            if not os.path.exists(DATA_PATH):
                logger.warning(f"Data file {DATA_PATH} does not exist. Starting with empty dataset.")
                self.chunks = []
                self.is_fitted = False
                return False

            with open(DATA_PATH, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

            logger.info(f"Loaded {len(self.chunks)} documents from {DATA_PATH}")

            # Try to load existing FAISS index + metadata
            vector_exists = os.path.exists(VECTOR_DB_PATH)
            meta_exists = os.path.exists(f"{VECTOR_DB_PATH}.meta")

            if vector_exists and meta_exists:
                ok = self._load_vector_db()
                if not ok:
                    logger.info("Existing vector DB invalid -> rebuilding.")
                    ok = self._build_vector_db()
            else:
                ok = self._build_vector_db()

            self.is_fitted = ok
            return ok

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.chunks = []
            self.is_fitted = False
            return False

    def _load_vector_db(self):
        """Load FAISS index and saved metadata (embedding vectors)."""
        try:
            # Load index
            self.vector_index = faiss.read_index(VECTOR_DB_PATH)

            # Load metadata
            with open(f"{VECTOR_DB_PATH}.meta", "rb") as f:
                meta = pickle.load(f)

            self.embedding_vectors = meta.get("embedding_vectors", None)
            chunks_count = meta.get("chunks_count", None)

            # Basic integrity checks
            if self.embedding_vectors is None:
                logger.warning("Metadata does not contain embedding_vectors -> rebuild required.")
                return False

            if chunks_count is not None and chunks_count != len(self.chunks):
                logger.warning("Chunks count in metadata differs from JSON. Rebuild required.")
                return False

            if self.vector_index.ntotal != len(self.chunks):
                logger.warning("FAISS index size doesn't match chunk count. Rebuild required.")
                return False

            logger.info(f"Successfully loaded FAISS index with {self.vector_index.ntotal} vectors")
            return True

        except Exception as e:
            logger.error(f"Failed to load vector DB: {e}")
            # cleanup partial state
            self.vector_index = None
            self.embedding_vectors = None
            return False

    def _build_vector_db(self):
        """Build FAISS index from scratch using current self.chunks."""
        try:
            if not self.chunks:
                logger.warning("No documents available to build vector DB.")
                return False

            texts = self._texts_from_chunks(self.chunks)
            logger.info("Encoding documents to embeddings...")
            embeddings = self.model.encode(texts, show_progress_bar=True)
            embeddings = np.array(embeddings).astype("float32")
            self.embedding_vectors = embeddings

            # Create FAISS index (L2)
            dim = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatL2(dim)
            self.vector_index.add(embeddings)

            # Save index + metadata
            self._save_vector_db()
            logger.info(f"Built FAISS index with {self.vector_index.ntotal} vectors (dim={dim})")
            return True

        except Exception as e:
            logger.error(f"Error building vector DB: {e}")
            self.vector_index = None
            self.embedding_vectors = None
            return False

    def _save_vector_db(self):
        """Persist FAISS index and metadata (embedding vectors, counts)."""
        try:
            # Write faiss index
            faiss.write_index(self.vector_index, VECTOR_DB_PATH)

            # Save minimal metadata
            meta = {
                "embedding_vectors": self.embedding_vectors,
                "chunks_count": len(self.chunks),
                "last_updated_ts": time.time()
            }
            with open(f"{VECTOR_DB_PATH}.meta", "wb") as f:
                pickle.dump(meta, f)

            logger.info(f"Saved FAISS index to {VECTOR_DB_PATH} and metadata to {VECTOR_DB_PATH}.meta")
            return True
        except Exception as e:
            logger.error(f"Error saving vector DB: {e}")
            return False

    def add_documents(self, new_chunks):
        """
        Add new documents (list of dicts) to JSON and FAISS index.
        If not fitted yet, it rebuilds the index from all chunks.
        """
        if not new_chunks:
            logger.warning("No new chunks provided.")
            return False

        try:
            # Append to in-memory chunks and persist JSON immediately
            original_count = len(self.chunks)
            self.chunks.extend(new_chunks)
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
            logger.info(f"Appended {len(new_chunks)} documents to {DATA_PATH} (total now {len(self.chunks)})")

            # If not fitted, build full DB
            if not self.is_fitted or self.vector_index is None:
                return self._build_vector_db()

            # Otherwise, encode only new texts and add to FAISS + metadata
            new_texts = self._texts_from_chunks(new_chunks)
            new_embeddings = self.model.encode(new_texts, show_progress_bar=False)
            new_embeddings = np.array(new_embeddings).astype("float32")

            # Add to faiss index
            self.vector_index.add(new_embeddings)

            # Update embedding_vectors
            if self.embedding_vectors is None:
                self.embedding_vectors = new_embeddings
            else:
                self.embedding_vectors = np.vstack([self.embedding_vectors, new_embeddings])

            # Persist updated index & metadata
            self._save_vector_db()
            logger.info(f"Added {len(new_chunks)} vectors to FAISS (was {original_count}, now {self.vector_index.ntotal})")
            self.is_fitted = True
            return True

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def _vector_search(self, query, top_n=TOP_N_RESULTS):
        """Return top_n matches for the query as [(doc_dict, score), ...]. Score is similarity in (0,1]."""
        if self.vector_index is None or self.vector_index.ntotal == 0:
            logger.warning("Vector index is not initialized or empty.")
            return []

        # Encode query
        q_emb = self.model.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb).astype("float32").reshape(1, -1)

        # k cannot exceed ntotal
        k = min(top_n, self.vector_index.ntotal)
        distances, indices = self.vector_index.search(q_emb, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            dist = float(distances[0][i])
            # Convert L2 distance to a normalized similarity score: s = 1 / (1 + dist)
            similarity = 1.0 / (1.0 + dist)
            doc = self.chunks[idx] if idx < len(self.chunks) else {}
            result = {
                "index": int(idx),
                "distance": dist,
                "similarity": similarity,
                "document": doc
            }
            results.append(result)
        return results

    def search(self, query: str, top_n: int = TOP_N_RESULTS):
        """
        Public search method (embedding-only).
        Returns list of result dicts sorted by best similarity.
        """
        if not self.is_fitted:
            logger.warning("SearchService not fitted. Attempting to (re)build vector DB.")
            if not self._build_vector_db():
                logger.error("Cannot search because vector DB could not be built.")
                return []

        return self._vector_search(query, top_n=top_n)

    def format_search_results(self, results):
        """Return a human-friendly string list from results (optional)."""
        formatted = []
        for i, r in enumerate(results, start=1):
            doc = r.get("document", {})
            titre = doc.get("titre", doc.get("id", f"doc_{r.get('index')}"))
            sim = r.get("similarity", 0.0)
            formatted.append(f"{i}. [{sim:.4f}] {titre}")
        return formatted
