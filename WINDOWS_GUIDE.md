# Windows & VS Code Implementation Guide

This guide provides step-by-step instructions to run the **PostgreSQL 16 + pgvector + Groq RAG Prototype** on **Windows** using **VS Code**.

---

## Overview

The main `README.md` is tailored for Linux (Ubuntu). On Windows, the primary difference is setting up **PostgreSQL with the `pgvector` extension** and activating Python environments in **PowerShell / CMD**.

There are 3 main ways to run this project on Windows:

1. **Option A: Docker Desktop + VS Code (Recommended & Easiest)**  
   Runs PostgreSQL 16 with `pgvector` inside a container. No complex C compilation or manual DLL placement needed.
2. **Option B: WSL2 (Windows Subsystem for Linux)**  
   Runs a native Linux environment inside Windows. You can follow the standard `README.md` directly.
3. **Option C: Native Windows PostgreSQL 16**  
   Installs PostgreSQL natively on Windows and copies/compiles `pgvector` binaries manually.

---

## Option A: Docker Desktop + VS Code (Recommended)

### Prerequisites
- [VS Code](https://code.visualstudio.com/) installed.
- [Python 3.10+](https://www.python.org/downloads/) installed (check "Add python.exe to PATH" during setup).
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) installed and running.

---

### Step 1: Start PostgreSQL + pgvector Container

Open **PowerShell** or VS Code Terminal and run:

```powershell
docker run -d `
  --name rag_postgres `
  -e POSTGRES_USER=rag_user `
  -e POSTGRES_PASSWORD=rag_password `
  -e POSTGRES_DB=ragdb `
  -p 5432:5432 `
  pgvector/pgvector:pg16
```

Verify that the container is running:

```powershell
docker ps
```

---

### Step 2: Set Up Python Environment in VS Code

1. Open the project folder in VS Code (`File` -> `Open Folder...` -> Select `rag_pgvector_groq`).
2. Open the built-in terminal (`Ctrl + \`` or `Terminal` -> `New Terminal`).
3. Set execution policy for the current session (if script activation is blocked by default Windows policies):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

4. You can use the automated PowerShell bootstrap script:

```powershell
.\scripts\bootstrap.ps1
```

*Or perform setup manually:*

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Create .env from template
Copy-Item .env.example .env
```

---

### Step 3: Configure Environment Variables

1. In VS Code, open `.env`.
2. Replace `YOUR_GROQ_API_KEY` (or the default key) with your actual Groq API key:

```env
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/ragdb
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=5
```

---

### Step 4: Select Python Interpreter in VS Code

1. Press `Ctrl + Shift + P` to open the Command Palette.
2. Type and select `Python: Select Interpreter`.
3. Choose `.venv\Scripts\python.exe` from the workspace folder.

---

### Step 5: Run the RAG Pipeline

Make sure your terminal prompt is at the **project root folder** (`rag_pgvector_groq`).  
If you are inside `scripts`, navigate back to root first:
```powershell
cd D:\BYTEHUBBLE\rag_pgvector_groq
```

In the active VS Code PowerShell terminal (`.venv` activated):

1. **Initialize the Database Schema:**
   ```powershell
   python scripts/init_db.py
   ```
   *(Creates tables and vector extension if not present).*

2. **Generate 100 Sample Documents:**
   ```powershell
   python scripts/generate_sample_docs.py
   ```

3. **Ingest Documents:**
   ```powershell
   python scripts/ingest_documents.py
   ```

4. **Run Interactive Assistant:**
   ```powershell
   python main.py
   ```

---

## Option B: WSL2 (Windows Subsystem for Linux)

If you prefer Linux commands natively on Windows:

1. Open PowerShell and run:
   ```powershell
   wsl --install
   ```
2. Restart your computer if prompted, then open Ubuntu terminal.
3. Install the **WSL Extension** in VS Code.
4. In Ubuntu terminal, clone/navigate to project folder and run:
   ```bash
   code .
   ```
5. Follow the standard Linux instructions in `README.md`.

---

## Option C: Native Windows PostgreSQL 16 Setup

If you cannot use Docker Desktop or WSL2:

1. Install **PostgreSQL 16** via the EDB Windows Installer.
2. Install **pgvector** on Windows:
   - Download the latest pre-built Windows binaries (`pgvector` release `.zip` matching PG16).
   - Copy `vector.dll` into `C:\Program Files\PostgreSQL\16\lib`.
   - Copy `vector.control` and `vector--*.sql` into `C:\Program Files\PostgreSQL\16\share\extension`.
3. Open `sql shell (psql)` or `pgAdmin 4` and create the user/database:
   ```sql
   CREATE USER rag_user WITH PASSWORD 'rag_password';
   CREATE DATABASE ragdb OWNER rag_user;
   \c ragdb
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Follow **Step 2 to Step 5** from Option A to configure Python and run the app.

---

## VS Code Debugging Features

This repository includes pre-configured VS Code Launch Configurations in `.vscode/launch.json`.

To run or debug scripts visually in VS Code:
1. Open the **Run and Debug** view (`Ctrl + Shift + D`).
2. Select one of the launch target configurations:
   - `Run Main RAG CLI`
   - `Init Database`
   - `Generate Sample Docs`
   - `Ingest Documents`
3. Press `F5` to start debugging with breakpoints enabled!

---

## Common Windows Troubleshooting

### 1. PowerShell Script Execution Error (`running scripts is disabled on this system`)
**Fix:** Run this command in your PowerShell terminal before activating `.venv`:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### 2. Database Connection Error (`connection to server at "localhost", port 5432 failed`)
- Check if Docker container is running (`docker ps`).
- If port 5432 is already occupied by a local PostgreSQL installation, run Docker on a different host port (e.g. `-p 5433:5432`) and update `DATABASE_URL` in `.env` to port `5433`.

### 3. Missing `pgvector` Extension Error
- Ensure you used the `pgvector/pgvector:pg16` image for Docker, or created `CREATE EXTENSION IF NOT EXISTS vector;` in PostgreSQL.

---
