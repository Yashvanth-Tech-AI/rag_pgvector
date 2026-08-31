# pgvector-rag-engine: High-Performance RAG Engine

A complete, end-to-end RAG (Retrieval-Augmented Generation) application built with:

- **PostgreSQL 16 + pgvector** (Hosted on AWS EC2 Ubuntu Server)
- **Local Client**: VS Code on Windows (PowerShell)
- **Python 3.10+**
- **Sentence Transformers** (`all-MiniLM-L6-v2`)
- **Groq API** (`llama-3.3-70b-versatile`)

---

## Architecture Diagram

```text
Documents (data/documents/)
   |
   v
Text Extraction & Cleaning
   |
   v
Chunking (800 chars / 120 overlap)
   |
   v
Local Embedding Model (all-MiniLM-L6-v2 -> 384 dimensions)
   |
   v
PostgreSQL 16 + pgvector (AWS EC2 Server)
   |
   |  <--- Remote Connection over Port 5432
   v
User Question (VS Code Terminal)
   |
   v
Query Embedding
   |
   v
pgvector Cosine Similarity Search (<=>)
   |
   v
Top-K Context Chunks
   |
   v
Grounded Prompt Construction
   |
   v
Groq API (Llama 3.3 70B)
   |
   v
Generated Answer + Source References
```

---

# Part 1: Setup PostgreSQL 16 + pgvector on AWS EC2 Server

SSH into your Ubuntu EC2 instance and run the following commands to install PostgreSQL 16 and the `pgvector` extension.

### Step 1.1: Install System Prerequisites

> [!NOTE]
> This step installs only the required system tools (Python, Git, curl, etc.).
> **PostgreSQL 16 itself is installed in Step 1.2** — do not add `postgresql` here to avoid duplicate installs.

```bash
sudo apt update
sudo apt install -y python3 python3-pip git curl ca-certificates
```

### Step 1.2: Install PostgreSQL 16 + pgvector Extension
Choose **one** of the following methods. Each method installs both PostgreSQL 16 and the `pgvector` extension:

```bash
# Option A: Automated script (Recommended — installs PostgreSQL 16 + pgvector in one step)
chmod +x scripts/setup_ubuntu_pgvector.sh
./scripts/setup_ubuntu_pgvector.sh

# Option B: Manual APT installation (if PostgreSQL 16 is already installed, just adds pgvector)
sudo apt install -y postgresql-16-pgvector

# Option C: Build pgvector from source (use if APT package is unavailable)
sudo apt install -y build-essential postgresql-server-dev-16
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

> [!TIP]
> **Option A** is the recommended path — it handles the full PostgreSQL 16 + pgvector install automatically and validates your environment. Use Option B or C only if you already have PostgreSQL 16 installed.

---

# Part 2: Configure EC2 PostgreSQL Server for Remote Connections

Perform these steps on your **AWS EC2 Ubuntu Server** *after* `pgvector` is installed, so that your local **Windows VS Code** environment can connect remotely.

### Step 2.1: Configure AWS Security Group (AWS Management Console)
1. Log in to the **AWS Console** and navigate to **EC2 > Instances > Security Groups**.
2. Select the Security Group attached to your EC2 instance.
3. Under **Inbound Rules**, click **Edit inbound rules**.
4. Add the following rule:
   - **Type**: `PostgreSQL` (or `Custom TCP`)
   - **Port Range**: `5432`
   - **Source**: `My IP` (Recommended for security) or `0.0.0.0/0` (Allows remote connections from any IP).
5. Click **Save rules**.

### Step 2.2: Update `postgresql.conf` to Listen on All Interfaces
Edit the main PostgreSQL configuration file on EC2:

```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Find the `listen_addresses` line (around line 60) and update it from `'localhost'` to `'*'`:
```ini
listen_addresses = '*'
```
*Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).*

### Step 2.3: Configure Remote Authentication in `pg_hba.conf`
Edit the PostgreSQL Host-Based Authentication configuration file:

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Scroll to the bottom of the file and add the following entry to allow remote access for `rag_user`:
```text
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    ragdb           rag_user        0.0.0.0/0               scram-sha-256
```
*(Note: If using md5 authentication, replace `scram-sha-256` with `md5`).*

### Step 2.4: Allow Firewall Port & Restart PostgreSQL
Allow port 5432 through the Ubuntu UFW firewall and restart the PostgreSQL service:

```bash
sudo ufw allow 5432/tcp
sudo systemctl restart postgresql
```

### Step 2.5: Create Database, User, and Enable Vector Extension on EC2

> [!IMPORTANT]
> **This is a one-time EC2 server setup step.** Run these SQL commands directly on your EC2 instance as the `postgres` superuser.
> This creates the database and user that your application will connect to.
>
> ⚠️ **Do not confuse this with Step 3.4** (`python scripts/init_db.py`) — that step runs **on your local Windows machine** and creates the application *tables* (`documents`, `document_chunks`) inside the database you create here.

Log in to PostgreSQL as `postgres` superuser on EC2:

```bash
sudo -u postgres psql
```

Run the following SQL statements:
```sql
-- Create dedicated application user
CREATE USER rag_user WITH PASSWORD 'rag_password';

-- Create database owned by rag_user
CREATE DATABASE ragdb OWNER rag_user;

-- Connect to ragdb database
\c ragdb

-- Enable vector extension (required for pgvector similarity search)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify vector extension is active
\dx

-- Exit psql
\q
```

> [!NOTE]
> After completing this step, your EC2 PostgreSQL server is fully configured. Switch to your **local Windows machine** for Part 3 to set up the Python application and create the schema tables.

---

# Part 3: Run Complete Application from Windows VS Code

Now switch to your local **Windows machine** and open **VS Code**. All commands below are run in the **VS Code Built-in PowerShell Terminal** (`Ctrl + ~`).

### Step 3.1: Open VS Code Terminal & Set Execution Policy
Open your project folder in VS Code (`File > Open Folder... > pgvector-rag-engine`).  
Open the terminal (`Terminal > New Terminal` or `Ctrl + ~`).

If script execution is blocked on Windows, allow script execution for the current session:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

---

### Step 3.2: Set Up Python Virtual Environment & Install Dependencies

**Option A: Automated Setup (Recommended)**
```powershell
.\scripts\bootstrap.ps1
```

**Option B: Manual Setup**
```powershell
# 1. Create Python virtual environment
python -m venv .venv

# 2. Activate virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip & install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Copy environment configuration template
Copy-Item .env.example .env
```

---

### Step 3.3: Configure Local `.env` File
In VS Code, open `.env` from the file explorer and set your **EC2 Public IP** and **Groq API Key**:

```env
# EC2 Remote PostgreSQL Connection:
DATABASE_URL=postgresql://rag_user:rag_password@<YOUR_EC2_PUBLIC_IP>:5432/ragdb

# Groq API Credentials:
GROQ_API_KEY=gsk_your_actual_groq_api_key_here

# Model & Chunking Parameters:
LLM_MODEL=qwen/qwen3.6-27b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=5
```

### Step 3.4: Initialize Database Schema
In the activated VS Code PowerShell terminal (`.venv`), run:

```powershell
python scripts/init_db.py
```
*Creates `documents` table and `document_chunks` table with `VECTOR(384)` embedding column on your EC2 PostgreSQL database.*

---

### Step 3.5: Generate 100 Sample Documents
To generate test document files in `data/documents/`:

```powershell
python scripts/generate_sample_docs.py
```
*(You can also place your own `.pdf`, `.docx`, `.txt`, or `.md` files in `data/documents/`).*

---

### Step 3.6: Ingest Documents into EC2 Vector Database
Process, chunk, embed, and store document vectors into EC2 PostgreSQL:

```powershell
python scripts/ingest_documents.py
```

*Pipeline summary:*
```text
Document Extraction -> Text Cleaning -> Chunking -> Embedding -> EC2 PostgreSQL
```
*(Duplicate documents are automatically skipped using SHA-256 hashes).*

---

### Step 3.7: Verify Ingested Data in PostgreSQL
Connect remotely using `psql` from VS Code PowerShell:

```powershell
psql -U rag_user -d ragdb -h <YOUR_EC2_PUBLIC_IP>
```

Run SQL queries:
```sql
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM document_chunks;

SELECT
    d.filename,
    c.chunk_index,
    LEFT(c.content, 100)
FROM document_chunks c
JOIN documents d
  ON d.document_id = c.document_id
LIMIT 10;

\q
```

---

### Step 3.8: Launch Streamlit Web UI Dashboard
Launch the interactive Streamlit Web UI:

```powershell
streamlit run main.py
```
*(Or simply run `python main.py` in VS Code terminal, which automatically launches the Streamlit Web Dashboard in your browser).*

#### Web Dashboard Features:
- 💬 **Interactive RAG Chat Assistant**: Ask questions with full conversation history, view retrieved context chunks with similarity scores, and test sample questions.
- 📚 **Document Management & Ingestion**: Drag-and-drop file upload (`.txt`, `.pdf`, `.docx`, `.md`), trigger ingestion directly from the UI, and view database records.
- 🔍 **pgvector Search Explorer**: Test raw vector similarity retrieval directly from EC2 PostgreSQL without calling the LLM.
- 🛠️ **Live System Status**: Real-time PostgreSQL EC2 connection indicator, total document & vector chunk counters, and architecture reference.

*(Note: To run in terminal CLI mode instead, use `python main.py --cli`).*

---

# Project Structure

```text
pgvector-rag-engine/
├── app/
│   ├── config.py             # Loads environment variables from .env
│   ├── database.py           # PostgreSQL connection pool (psycopg2)
│   ├── document_loader.py    # Text, PDF, DOCX, MD loader
│   ├── embeddings.py         # SentenceTransformers embedding engine
│   ├── groq_client.py        # Groq LLM API integration
│   ├── prompt_builder.py     # Grounded context prompt constructor
│   ├── rag_pipeline.py       # End-to-end RAG orchestrator
│   ├── retriever.py          # Vector retrieval logic
│   ├── text_splitter.py      # Overlapping text chunker
│   └── vector_store.py       # pgvector similarity search queries
├── data/
│   └── documents/            # Target folder for ingested documents
├── scripts/
│   ├── bootstrap.ps1         # PowerShell bootstrap script for Windows
│   ├── bootstrap.sh          # Bash bootstrap script for Linux/macOS
│   ├── generate_sample_docs.py # Generates 100 synthetic text docs
│   ├── ingest_documents.py   # Document ingestion CLI
│   ├── init_db.py            # Database schema setup script
│   └── setup_ubuntu_pgvector.sh # EC2 pgvector setup script
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── main.py                   # Interactive RAG CLI
├── ARCHITECTURE.md           # Technical architecture documentation
└── README.md                 # Master documentation & step-by-step guide
```

---

# Component Summary

* **`document_loader.py`**: Extracts text from `.txt`, `.pdf`, `.docx`, `.md`.
* **`text_splitter.py`**: Splits text into sliding window chunks (`800` chars, `120` overlap).
* **`embeddings.py`**: Generates 384-dimensional vector embeddings via `sentence-transformers/all-MiniLM-L6-v2`.
* **`vector_store.py`**: Executes cosine distance similarity searches (`<=>`) in EC2 PostgreSQL.
* **`retriever.py`**: Fetches top-K relevant text chunks for a query.
* **`prompt_builder.py`**: Wraps retrieved context into a grounded prompt for LLM generation.
* **`groq_client.py`**: Queries Groq API with `llama-3.3-70b-versatile`.
* **`rag_pipeline.py`**: Connects retriever, prompt builder, and Groq client.
* **`main.py`**: Interactive VS Code terminal interface.
