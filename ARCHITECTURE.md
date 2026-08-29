# Architecture Walkthrough

## Components

### document_loader.py
Responsible only for turning supported files into plain text.

### text_splitter.py
Turns large text into overlapping chunks so retrieval can return focused passages.

### embeddings.py
Uses one local embedding model for both documents and queries.

### vector_store.py
Owns PostgreSQL persistence and pgvector similarity search.

### retriever.py
Connects query embedding to vector search.

### prompt_builder.py
Turns retrieved chunks into grounded LLM context.

### groq_client.py
Owns the external LLM API call.

### rag_pipeline.py
Orchestrates retrieval + context + generation.

### main.py
Provides the simple CLI.

## Data flow

Ingestion:

file
→ extract text
→ clean
→ chunk
→ embed
→ insert document
→ insert chunks + vectors

Question:

question
→ embed
→ pgvector cosine search
→ top-K chunks
→ context
→ Groq
→ answer + sources
