"""PostgreSQL + pgvector storage and similarity retrieval."""

import hashlib
import json
from pathlib import Path

from app.database import Database


def content_hash(text: str) -> str:
    """Create a stable SHA-256 hash for duplicate document detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vector_literal(vector: list[float]) -> str:
    """Convert a Python vector into pgvector's '[1,2,3]' representation."""
    return "[" + ",".join(str(float(x)) for x in vector) + "]"


class VectorStore:
    """Data-access layer for documents, chunks, and vector search."""

    def __init__(self, database: Database):
        self.database = database

    def is_document_exists(self, filename: str, content: str) -> bool:
        """Check if a document with the same filename or content hash already exists in PostgreSQL."""
        digest = content_hash(content)
        with self.database.connect() as conn:
            existing = conn.execute(
                "SELECT document_id FROM documents WHERE content_hash = %s OR filename = %s",
                (digest, filename),
            ).fetchone()
            return existing is not None

    def add_document(
        self,
        filename: str,
        content: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> bool:
        """Insert a document and its chunks unless the document already exists."""
        digest = content_hash(content)

        with self.database.connect() as conn:
            existing = conn.execute(
                "SELECT document_id FROM documents WHERE content_hash = %s",
                (digest,),
            ).fetchone()

            if existing:
                return False

            document = conn.execute(
                """
                INSERT INTO documents
                    (filename, title, source, document_type, content_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING document_id
                """,
                (
                    filename,
                    Path(filename).stem,
                    filename,
                    Path(filename).suffix.lower().lstrip("."),
                    digest,
                ),
            ).fetchone()

            document_id = document["document_id"]

            for index, (chunk, embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                conn.execute(
                    """
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (
                        document_id,
                        index,
                        chunk,
                        vector_literal(embedding),
                    ),
                )

            conn.commit()

        return True

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict]:
        """Return the most semantically similar chunks using cosine distance."""
        query_vector = vector_literal(query_embedding)

        sql = """
        SELECT
            c.chunk_id,
            c.document_id,
            c.chunk_index,
            c.content,
            d.filename,
            d.title,
            1 - (c.embedding <=> %s::vector) AS similarity
        FROM document_chunks c
        JOIN documents d ON d.document_id = c.document_id
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """

        with self.database.connect() as conn:
            rows = conn.execute(
                sql,
                (query_vector, query_vector, top_k),
            ).fetchall()

        return [dict(row) for row in rows]
