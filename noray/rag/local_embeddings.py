import os


class LocalEmbeddings:
    """Provides local embedding generation using SentenceTransformers."""

    SUPPORTED_MODELS = {
        "bge-m3": "BAAI/bge-m3",
        "jina-v4": "jinaai/jina-embeddings-v4-base-en",
        "nomic-text": "nomic-ai/nomic-embed-text-v1.5",
        "e5-multilingual": "intfloat/multilingual-e5-large",
    }

    def __init__(self, model_key: str = None):
        self.model_key = model_key or os.getenv("EMBEDDING_MODEL_KEY", "bge-m3")

        if self.model_key not in self.SUPPORTED_MODELS:
            print(f"Warning: {self.model_key} not in supported list. Defaulting to BAAI/bge-m3.")
            self.model_key = "bge-m3"

        self.model_name = self.SUPPORTED_MODELS[self.model_key]
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install it with: pip install sentence-transformers"
                )
            print(f"Loading local embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name, trust_remote_code=True)
            print(f"[OK] Embedding model {self.model_name} loaded successfully.")

    @property
    def model(self):
        self._ensure_model()
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.model_key == "nomic-text":
            texts = [f"search_document: {t}" for t in texts]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if self.model_key == "nomic-text":
            text = f"search_query: {text}"
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()


_embedding_instance = None


def get_embeddings_model() -> LocalEmbeddings:
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = LocalEmbeddings()
    return _embedding_instance
