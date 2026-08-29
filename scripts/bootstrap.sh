#!/usr/bin/env bash
set -euo pipefail

# Complete application bootstrap after PostgreSQL 16 + pgvector are installed.

echo "=== RAG Prototype bootstrap ==="

if [[ ! -f ".env" ]]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "IMPORTANT: edit .env and add your GROQ_API_KEY."
fi

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python scripts/init_db.py

echo
echo "Bootstrap complete."
echo
echo "Generate 100 sample documents:"
echo "  python scripts/generate_sample_docs.py"
echo
echo "Ingest documents:"
echo "  python scripts/ingest_documents.py"
echo
echo "Run RAG:"
echo "  python main.py"
