"""Prompt construction for grounded RAG answers."""

SYSTEM_PROMPT = """
You are a grounded RAG assistant.

Answer the user's question using the retrieved context provided by the
application.

Rules:
1. Prefer the retrieved context over your general knowledge.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information, say:
   "I don't have enough information in the retrieved documents to answer that."
4. You may synthesize information across multiple retrieved sources.
5. When making factual claims, cite the source filename in square brackets.
6. Do not claim to have read documents that were not provided in the context.
7. Keep the answer clear and useful.
""".strip()


def build_context(results: list[dict]) -> str:
    """Turn retrieved database rows into labeled context for the LLM."""
    if not results:
        return "No relevant documents were retrieved."

    sections = []

    for result in results:
        sections.append(
            f"SOURCE: {result['filename']} "
            f"(chunk {result['chunk_index']}, "
            f"similarity={result['similarity']:.4f})\n"
            f"{result['content']}"
        )

    return "\n\n---\n\n".join(sections)


def build_user_prompt(question: str, context: str) -> str:
    """Build the final user message sent to the Groq model."""
    return f"""
Answer the question using ONLY the retrieved context below.

QUESTION:
{question}

RETRIEVED CONTEXT:
{context}
""".strip()
