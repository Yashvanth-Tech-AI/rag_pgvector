"""Interactive CLI for the prototype RAG system."""

from app.config import get_settings
from app.database import Database
from app.embeddings import EmbeddingService
from app.groq_client import GroqLLM
from app.rag_pipeline import RAGPipeline
from app.retriever import Retriever
from app.vector_store import VectorStore


def build_pipeline() -> RAGPipeline:
    """Create all application components and wire them together."""
    settings = get_settings()

    database = Database(settings.database_url)
    embeddings = EmbeddingService(settings.embedding_model)
    vector_store = VectorStore(database)
    retriever = Retriever(
        embeddings=embeddings,
        vector_store=vector_store,
        top_k=settings.top_k,
    )
    llm = GroqLLM(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
    )

    return RAGPipeline(retriever=retriever, llm=llm)


def main() -> None:
    """Start the interactive question-answer loop."""
    pipeline = build_pipeline()

    print("\nRAG Assistant")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Ask a question: ").strip()

        if question.lower() in {"exit", "quit"}:
            break

        if not question:
            continue

        result = pipeline.ask(question)

        print("\nANSWER")
        print(result["answer"])

        print("\nSOURCES")
        for source in result["sources"]:
            print(
                f"- {source['filename']} | "
                f"chunk={source['chunk_index']} | "
                f"similarity={source['similarity']:.4f}"
            )

        print()


if __name__ == "__main__":
    main()
