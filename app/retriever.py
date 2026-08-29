"""Retrieval layer: converts a question into a vector search."""

from app.embeddings import EmbeddingService
from app.vector_store import VectorStore


class Retriever:
    """Coordinates query embedding and pgvector similarity search."""

    def __init__(
        self,
        embeddings: EmbeddingService,
        vector_store: VectorStore,
        top_k: int,
    ):
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, question: str) -> list[dict]:
        """Embed the question and retrieve the top-K relevant chunks."""
        query_embedding = self.embeddings.embed_text(question)

        return self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=self.top_k,
        )
