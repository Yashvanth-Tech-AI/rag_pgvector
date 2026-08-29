# PowerShell Bootstrap Script for Windows

Write-Host "=== RAG Prototype Bootstrap (Windows PowerShell) ===" -ForegroundColor Green

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    Write-Host "IMPORTANT: Edit .env and replace GROQ_API_KEY with your actual API key." -ForegroundColor Red
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Activating virtual environment and installing requirements..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Initializing database schema..." -ForegroundColor Cyan
try {
    & .\.venv\Scripts\python.exe scripts/init_db.py
} catch {
    Write-Host "Database initialization failed. Ensure PostgreSQL / Docker pgvector container is running!" -ForegroundColor Red
}

Write-Host "`nBootstrap completed!" -ForegroundColor Green
Write-Host "Next steps in VS Code terminal:" -ForegroundColor Yellow
Write-Host "  1. Set your GROQ_API_KEY in .env"
Write-Host "  2. Generate sample docs:  python scripts/generate_sample_docs.py"
Write-Host "  3. Ingest documents:      python scripts/ingest_documents.py"
Write-Host "  4. Run RAG Assistant:     python main.py"
