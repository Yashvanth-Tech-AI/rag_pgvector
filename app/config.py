"""Central configuration for the prototype RAG application."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_url: str
    groq_api_key: str
    llm_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int


def get_settings() -> Settings:
    """Read configuration and fail early when required values are missing."""
    database_url = os.getenv("DATABASE_URL")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not database_url:
        raise ValueError("DATABASE_URL is missing from .env")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from .env")

    return Settings(
        database_url=database_url,
        groq_api_key=groq_api_key,
        llm_model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
        top_k=int(os.getenv("TOP_K", "5")),
    )
