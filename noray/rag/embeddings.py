import os


class BaseEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

class LocalEmbedder(BaseEmbedder):
    """Uses local SentenceTransformers to generate dense vector embeddings locally."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

    def _lazy_init(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._lazy_init()
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]


class OpenAIEmbedder(BaseEmbedder):
    """Uses OpenAI API to generate embeddings."""
    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx
        if not self.api_key:
            raise ValueError("OpenAI API key missing. Set OPENAI_API_KEY environment variable.")

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model_name
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Extract embeddings in sorted order by index
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]


class VoyageEmbedder(BaseEmbedder):
    """Uses Voyage AI API to generate embeddings."""
    def __init__(self, model_name: str = "voyage-3", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY", "")

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx
        if not self.api_key:
            raise ValueError("Voyage API key missing. Set VOYAGE_API_KEY environment variable.")

        url = "https://api.voyageai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model_name
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"] # Voyage returns simple array of lists of floats


class JinaEmbedder(BaseEmbedder):
    """Uses Jina AI API to generate embeddings."""
    def __init__(self, model_name: str = "jina-embeddings-v2-base-en", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx
        if not self.api_key:
            raise ValueError("Jina API key missing. Set JINA_API_KEY environment variable.")

        url = "https://api.jina.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model_name
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Sort by index if returned inside dict list
            if isinstance(data["data"][0], dict):
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
            return data["data"]


class EmbeddingsManager:
    """Manager that resolves and loads embedding models based on environment variables or parameters."""
    _instance: BaseEmbedder | None = None

    @staticmethod
    def get_embedder(provider: str = None, model_name: str = None) -> BaseEmbedder:
        if EmbeddingsManager._instance is not None:
            return EmbeddingsManager._instance

        provider = provider or os.getenv("EMBEDDINGS_PROVIDER", "local").lower()

        if provider == "openai":
            model = model_name or os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
            EmbeddingsManager._instance = OpenAIEmbedder(model_name=model)
        elif provider == "voyage":
            model = model_name or os.getenv("EMBEDDINGS_MODEL", "voyage-3")
            EmbeddingsManager._instance = VoyageEmbedder(model_name=model)
        elif provider == "jina":
            model = model_name or os.getenv("EMBEDDINGS_MODEL", "jina-embeddings-v2-base-en")
            EmbeddingsManager._instance = JinaEmbedder(model_name=model)
        else:
            # Default to local SentenceTransformers
            model = model_name or os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
            EmbeddingsManager._instance = LocalEmbedder(model_name=model)

        return EmbeddingsManager._instance
