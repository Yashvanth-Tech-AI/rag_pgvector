"""Read documents, chunk them, embed them, and store them in pgvector."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.database import Database
from app.document_loader import clean_text, load_document
from app.embeddings import EmbeddingService
from app.text_splitter import split_text
from app.vector_store import VectorStore


def ingest_directory(directory: Path) -> None:
    """Ingest all supported files under the supplied directory."""
    settings = get_settings()
    database = Database(settings.database_url)
    store = VectorStore(database)
    embeddings = EmbeddingService(settings.embedding_model)

    supported = {".txt", ".md", ".pdf", ".docx"}
    files = [
        path for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in supported
    ]

    print(f"Found {len(files)} supported documents.")

    for path in files:
        print(f"\nProcessing: {path.name}")

        raw_text = load_document(path)
        text = clean_text(raw_text)

        if not text:
            print("  Skipped: document contains no extractable text.")
            continue

        # Fast duplicate check before embedding
        if store.is_document_exists(path.name, text):
            print("  Skipped: duplicate document already exists in PostgreSQL.")
            continue

        chunks = split_text(
            text,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        print(f"  Created {len(chunks)} chunks.")

        vectors = embeddings.embed_documents(chunks)

        inserted = store.add_document(
            filename=path.name,
            content=text,
            chunks=chunks,
            embeddings=vectors,
        )

        if inserted:
            print("  Inserted into PostgreSQL.")
        else:
            print("  Skipped duplicate document.")


if __name__ == "__main__":
    ingest_directory(PROJECT_ROOT / "data" / "documents")
