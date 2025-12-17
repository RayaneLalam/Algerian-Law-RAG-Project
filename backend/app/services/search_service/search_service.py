import json
import logging
import os
import time
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Configuration
DATA_PATH = "data/constitution.json"
METADATA_PATH = "data/constitution_metadata.json"
VECTOR_DB_PATH = "data/constitution.index"
TOP_N_RESULTS = 3

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchService:
    """
    Search service for the Algerian Constitution using vector embeddings.
    Works with two JSON files:
    - constitution.json: nested structure with titles/chapters/articles
    - constitution_metadata.json: flat list of article references
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

        # Model and storage
        self.embedding_model_name = embedding_model
        self.model = SentenceTransformer(self.embedding_model_name)

        # In-memory state
        self.constitution_data = None   # Full nested JSON structure
        self.metadata = []              # Flat list of article metadata
        self.chunks = []                # List of searchable article dicts
        self.embedding_vectors = None   # numpy array (n_documents, dim)
        self.vector_index = None        # faiss index
        self.is_fitted = False

        # Load on init
        self.load_data()

    def _extract_articles_from_constitution(self):
        """
        Extract individual articles from the nested constitution structure.
        Returns a list of article dicts with full context.
        """
        articles = []
        
        if not self.constitution_data:
            return articles
        
        titles = self.constitution_data.get("titles", [])
        
        for title in titles:
            title_number = title.get("title_number", "")
            title_name = title.get("title_name", "")
            
            for chapter in title.get("chapters", []):
                chapter_number = chapter.get("chapter_number", "")
                chapter_name = chapter.get("chapter_name", "")
                
                for article in chapter.get("articles", []):
                    article_number = article.get("article_number", "")
                    content = article.get("content", "")
                    
                    # Create enriched article dict
                    article_dict = {
                        "title": title_number,
                        "title_name": title_name,
                        "chapter": chapter_number,
                        "chapter_name": chapter_name,
                        "article": article_number,
                        "content": content,
                        "full_reference": f"Titre {title_number}, Chapitre {chapter_number}, Article {article_number}"
                    }
                    articles.append(article_dict)
        
        logger.info(f"Extracted {len(articles)} articles from constitution")
        return articles

    def _texts_from_chunks(self, chunks):
        """
        Convert article chunks to text strings for embedding.
        Prioritizes content, with minimal context.
        """
        texts = []
        for c in chunks:
            if isinstance(c, dict):
                content = c.get("content", "")
                
                # For short articles (< 50 chars), add minimal context
                # For longer articles, content alone is sufficient
                if len(content) < 50:
                    article_ref = f"Article {c.get('article', '')}"
                    combined = f"{article_ref}: {content}"
                else:
                    combined = content
                
                if not combined:
                    combined = json.dumps(c, ensure_ascii=False)
                texts.append(combined)
            else:
                texts.append(str(c))
        return texts

    def load_data(self):
        """Load constitution JSON, metadata, and vector DB."""
        try:
            # Load main constitution file
            if not os.path.exists(DATA_PATH):
                logger.warning(f"Data file {DATA_PATH} does not exist.")
                self.chunks = []
                self.is_fitted = False
                return False

            with open(DATA_PATH, "r", encoding="utf-8") as f:
                self.constitution_data = json.load(f)
            logger.info(f"Loaded constitution from {DATA_PATH}")

            # Load metadata (optional, for reference)
            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded {len(self.metadata)} article metadata entries")

            # Extract articles as searchable chunks
            self.chunks = self._extract_articles_from_constitution()
            
            if not self.chunks:
                logger.warning("No articles extracted from constitution")
                self.is_fitted = False
                return False

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
                logger.warning("Chunks count in metadata differs from extracted articles. Rebuild required.")
                return False

            if self.vector_index.ntotal != len(self.chunks):
                logger.warning("FAISS index size doesn't match chunk count. Rebuild required.")
                return False

            logger.info(f"Successfully loaded FAISS index with {self.vector_index.ntotal} vectors")
            return True

        except Exception as e:
            logger.error(f"Failed to load vector DB: {e}")
            self.vector_index = None
            self.embedding_vectors = None
            return False

    def _build_vector_db(self):
        """Build FAISS index from scratch using current chunks."""
        try:
            if not self.chunks:
                logger.warning("No articles available to build vector DB.")
                return False

            texts = self._texts_from_chunks(self.chunks)
            logger.info("Encoding articles to embeddings...")
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
        """Persist FAISS index and metadata."""
        try:
            faiss.write_index(self.vector_index, VECTOR_DB_PATH)

            meta = {
                "embedding_vectors": self.embedding_vectors,
                "chunks_count": len(self.chunks),
                "last_updated_ts": time.time()
            }
            with open(f"{VECTOR_DB_PATH}.meta", "wb") as f:
                pickle.dump(meta, f)

            logger.info(f"Saved FAISS index to {VECTOR_DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving vector DB: {e}")
            return False

    def _vector_search(self, query, top_n=TOP_N_RESULTS):
        """Return top_n matches for the query."""
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
        Public search method.
        Returns list of result dicts sorted by best similarity.
        """
        if not self.is_fitted:
            logger.warning("SearchService not fitted. Attempting to (re)build vector DB.")
            if not self._build_vector_db():
                logger.error("Cannot search because vector DB could not be built.")
                return []

        return self._vector_search(query, top_n=top_n)

    def format_search_results(self, results):
        """Return a human-friendly string list from results."""
        formatted = []
        for i, r in enumerate(results, start=1):
            doc = r.get("document", {})
            ref = doc.get("full_reference", f"Article {doc.get('article', '?')}")
            sim = r.get("similarity", 0.0)
            content_preview = doc.get("content", "")[:100]
            formatted.append(f"{i}. [{sim:.4f}] {ref}\n   {content_preview}...")
        return formatted

    def get_article_by_reference(self, title, chapter, article):
        """
        Retrieve a specific article by its reference.
        Returns the article dict or None if not found.
        """
        for chunk in self.chunks:
            if (chunk.get("title") == title and 
                chunk.get("chapter") == chapter and 
                chunk.get("article") == article):
                return chunk
        return None