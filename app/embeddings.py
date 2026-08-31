"""Local embedding generation using Sentence Transformers."""

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Loads one embedding model for both documents and user queries."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        """Convert one text string into a dense numerical vector."""
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        return vector.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Alias for embed_text to support query embedding."""
        return self.embed_text(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for many chunks efficiently."""
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return vectors.tolist()

    def dimension(self) -> int:
        """Return the embedding dimension expected by pgvector."""
        return self.model.get_sentence_embedding_dimension()
