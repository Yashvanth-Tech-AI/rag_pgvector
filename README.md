# RAG Prototype: PostgreSQL 16 + pgvector + Groq

A small, understandable RAG application built with:

- Ubuntu
- PostgreSQL 16
- pgvector
- Python
- Sentence Transformers
- Groq
- Llama 3.3 70B

This is intentionally a **prototype**, not an enterprise production platform.

> [!NOTE]
> **Windows Users**: If you are using Windows and VS Code, please refer to [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for full setup instructions (Docker Desktop / PowerShell / WSL2).

## Architecture

```text
Documents
   |
   v
Text Extraction
   |
   v
Text Cleaning
   |
   v
Chunking
   |
   v
Local Embedding Model
   |
   v
PostgreSQL 16 + pgvector
   |
   |
   v
User Question
   |
   v
Query Embedding
   |
   v
pgvector Cosine Similarity Search
   |
   v
Top-K Chunks
   |
   v
Grounded Prompt
   |
   v
Groq / Llama
   |
   v
Answer + Sources
```

# 1. Ubuntu prerequisites

The project expects PostgreSQL 16.

Verify:

```bash
psql --version
```

You should see PostgreSQL 16.x.

You also need:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl ca-certificates
```

# 2. Install PostgreSQL 16 + pgvector

The project now includes the installation script:

```bash
chmod +x scripts/setup_ubuntu_pgvector.sh
```

Run:

```bash
./scripts/setup_ubuntu_pgvector.sh
```

The script:

1. Checks that PostgreSQL 16 is installed.
2. Configures the PostgreSQL APT repository helper when required.
3. Installs the PostgreSQL-16-specific pgvector package.
4. Restarts PostgreSQL.
5. Verifies that `vector.control` exists.
6. Executes `CREATE EXTENSION vector`.
7. Displays the installed pgvector version.

The pgvector project documents the Ubuntu/Debian package as:

```bash
sudo apt install postgresql-16-pgvector
```

and distinguishes installation of the extension files from enabling the extension inside a database.

# 3. Create the RAG database and user

Run:

```bash
sudo -u postgres psql
```

Then:

```sql
CREATE USER rag_user WITH PASSWORD 'rag_password';
CREATE DATABASE ragdb OWNER rag_user;
\c ragdb
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

Verify:

```bash
psql -U rag_user -d ragdb -h localhost \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

# 4. Configure Python

From the project root:

```bash
./scripts/bootstrap.sh
```

This creates:

```text
.venv/
.env
```

and installs the Python requirements.

Alternatively, do it manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

# 5. Configure Groq

Edit:

```bash
nano .env
```

Set:

```text
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/ragdb
GROQ_API_KEY=YOUR_GROQ_API_KEY
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=5
```

Never commit `.env`.

# 6. Initialize the RAG schema

```bash
source .venv/bin/activate
python scripts/init_db.py
```

The application creates:

```text
documents
document_chunks
```

The vector column is:

```sql
embedding VECTOR(384)
```

The `384` matches:

```text
sentence-transformers/all-MiniLM-L6-v2
```

# 7. Generate 100 sample documents

If you do not have documents yet:

```bash
python scripts/generate_sample_docs.py
```

This creates 100 synthetic TXT files under:

```text
data/documents/
```

You can delete these and place your own:

- PDF
- DOCX
- TXT
- Markdown

files there.

# 8. Ingest documents

```bash
python scripts/ingest_documents.py
```

Pipeline:

```text
document
  |
  v
text extraction
  |
  v
clean text
  |
  v
chunks
  |
  v
embeddings
  |
  v
PostgreSQL
```

Duplicate documents are detected using a SHA-256 content hash.

# 9. Check the database

```bash
psql -U rag_user -d ragdb -h localhost
```

Run:

```sql
SELECT COUNT(*) FROM documents;
```

```sql
SELECT COUNT(*) FROM document_chunks;
```

```sql
SELECT
    d.filename,
    c.chunk_index,
    LEFT(c.content, 100)
FROM document_chunks c
JOIN documents d
  ON d.document_id = c.document_id
LIMIT 10;
```

# 10. Run the RAG application

```bash
python main.py
```

Example:

```text
RAG Assistant
Type 'exit' to quit.

Ask a question: What is PostgreSQL VACUUM used for?
```

The application:

```text
Question
   |
   v
Embedding
   |
   v
pgvector search
   |
   v
Top-K chunks
   |
   v
Context construction
   |
   v
Groq LLM
   |
   v
Answer + source filenames
```

# 11. Why pgvector is not indexed initially

The prototype contains approximately 100 documents.

For this size, exact nearest-neighbor search is sufficient and easier to understand.

When the chunk count becomes substantially larger, an HNSW index can be added:

```sql
CREATE INDEX idx_document_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops);
```

# 12. Important pgvector query

Retrieval uses cosine distance:

```sql
ORDER BY c.embedding <=> %s::vector
LIMIT %s
```

The application converts distance into a similarity-style score:

```sql
1 - (c.embedding <=> %s::vector)
```

# 13. Project structure

```text
rag_pgvector_groq/
|
âââ app/
â   âââ config.py
â   âââ database.py
â   âââ document_loader.py
â   âââ embeddings.py
â   âââ groq_client.py
â   âââ prompt_builder.py
â   âââ rag_pipeline.py
â   âââ retriever.py
â   âââ text_splitter.py
â   âââ vector_store.py
|
âââ data/
â   âââ documents/
|
âââ scripts/
â   âââ bootstrap.sh
â   âââ generate_sample_docs.py
â   âââ ingest_documents.py
â   âââ init_db.py
â   âââ setup_ubuntu_pgvector.sh
|
âââ tests/
âââ .env.example
âââ requirements.txt
âââ main.py
âââ ARCHITECTURE.md
âââ README.md
```

# 14. What each major component does

### document_loader.py

Extracts text from supported files.

### text_splitter.py

Breaks large documents into smaller overlapping chunks.

### embeddings.py

Converts chunks and questions into numerical vectors.

### vector_store.py

Stores vectors in PostgreSQL and performs similarity search.

### retriever.py

Connects question embedding to vector search.

### prompt_builder.py

Creates grounded context and the RAG prompt.

### groq_client.py

Calls the Groq-hosted LLM.

### rag_pipeline.py

Orchestrates the entire RAG process.

### main.py

Provides the interactive CLI.

# 15. Prototype limitations

This version intentionally does not include:

- authentication
- multi-tenancy
- hybrid search
- reranking
- conversation memory
- query rewriting
- distributed ingestion
- queues
- caching
- enterprise observability
- Kubernetes

Those should be added only after the core RAG pipeline is understood.

# 16. Next evolution

Recommended order:

```text
Basic RAG
   |
   v
HNSW
   |
   v
Metadata filtering
   |
   v
Hybrid search
   |
   v
Reranking
   |
   v
RAG evaluation
   |
   v
FastAPI
   |
   v
Streamlit
   |
   v
Conversation memory
   |
   v
Query rewriting
   |
   v
Multi-query RAG
   |
   v
Agentic RAG
```
