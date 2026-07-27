import os

from sentence_transformers import SentenceTransformer


class LocalEmbeddings:
    """Provides local embedding generation using SentenceTransformers."""

    # Recommended priority list
    SUPPORTED_MODELS = {
        "bge-m3": "BAAI/bge-m3",
        "jina-v4": "jinaai/jina-embeddings-v4-base-en",
        "nomic-text": "nomic-ai/nomic-embed-text-v1.5",
        "e5-multilingual": "intfloat/multilingual-e5-large"
    }

    def __init__(self, model_key: str = None):
        # Configure model based on env var or fallback priority
        self.model_key = model_key or os.getenv("EMBEDDING_MODEL_KEY", "bge-m3")

        if self.model_key not in self.SUPPORTED_MODELS:
            print(f"⚠ Warning: {self.model_key} not in supported list. Defaulting to BAAI/bge-m3.")
            self.model_key = "bge-m3"

        self.model_name = self.SUPPORTED_MODELS[self.model_key]
        print(f"Loading local embedding model: {self.model_name}...")

        # Load model using sentence-transformers (will download if not present)
        # trust_remote_code is needed for nomic and jina models
        self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
        print(f"[OK] Embedding model {self.model_name} loaded successfully.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document strings."""
        if not texts:
            return []

        # Add prefix for specific models if needed. Nomic usually needs 'search_document: '
        if self.model_key == "nomic-text":
            texts = [f"search_document: {t}" for t in texts]

        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        if self.model_key == "nomic-text":
            text = f"search_query: {text}"

        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

# Singleton instance for the app
_embedding_instance = None

def get_embeddings_model() -> LocalEmbeddings:
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = LocalEmbeddings()
    return _embedding_instance
