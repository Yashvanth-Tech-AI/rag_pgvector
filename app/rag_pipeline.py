"""End-to-end RAG orchestration."""

from app.groq_client import GroqLLM
from app.prompt_builder import (
    SYSTEM_PROMPT,
    build_context,
    build_user_prompt,
)
from app.retriever import Retriever


class RAGPipeline:
    """Coordinates retrieval, context construction, and generation."""

    def __init__(self, retriever: Retriever, llm: GroqLLM):
        self.retriever = retriever
        self.llm = llm

    def ask(self, question: str) -> dict:
        """Run one complete RAG question-answer cycle."""
        results = self.retriever.retrieve(question)
        context = build_context(results)
        prompt = build_user_prompt(question, context)

        answer = self.llm.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": results,
        }
