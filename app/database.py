"""PostgreSQL connection and schema management."""

import psycopg
from psycopg.rows import dict_row


class Database:
    """Small database wrapper used by the prototype."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def connect(self):
        """Open a PostgreSQL connection that returns rows as dictionaries."""
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def initialize(self) -> None:
        """Enable pgvector and create the RAG tables."""
        sql = """
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE IF NOT EXISTS documents (
            document_id BIGSERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT,
            source TEXT,
            document_type TEXT,
            content_hash TEXT UNIQUE NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id BIGSERIAL PRIMARY KEY,
            document_id BIGINT NOT NULL REFERENCES documents(document_id)
                ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(384) NOT NULL,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(document_id, chunk_index)
        );

        CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
            ON document_chunks(document_id);
        """
        with self.connect() as conn:
            conn.execute(sql)
            conn.commit()
