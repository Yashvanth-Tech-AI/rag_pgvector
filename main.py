"""Streamlit Web UI & CLI for pgvector-rag-engine (PostgreSQL 16 + pgvector + Groq)."""

import os
import sys
import time
import subprocess
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try importing Streamlit
try:
    # pyrefly: ignore [missing-import]
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from app.config import get_settings
from app.database import Database
from app.embeddings import EmbeddingService
from app.groq_client import GroqLLM
from app.rag_pipeline import RAGPipeline
from app.retriever import Retriever
from app.vector_store import VectorStore
from app.document_loader import load_document, clean_text
from app.text_splitter import split_text


# ==============================================================================
# Pipeline Builder (Cached for Performance)
# ==============================================================================
def get_pipeline(top_k: int = 5, model_name: str | None = None) -> RAGPipeline:
    """Create and wire all RAG pipeline components together."""
    settings = get_settings()
    db_url = settings.database_url
    llm_model = model_name or settings.llm_model

    database = Database(db_url)
    embeddings = EmbeddingService(settings.embedding_model)
    vector_store = VectorStore(database)
    retriever = Retriever(
        embeddings=embeddings,
        vector_store=vector_store,
        top_k=top_k,
    )
    llm = GroqLLM(
        api_key=settings.groq_api_key,
        model=llm_model,
    )

    return RAGPipeline(retriever=retriever, llm=llm)


def get_db_stats() -> dict:
    """Fetch live document and chunk counts from PostgreSQL."""
    try:
        settings = get_settings()
        database = Database(settings.database_url)
        with database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents;")
                doc_row = cur.fetchone()
                if doc_row is None:
                    doc_count = 0
                elif isinstance(doc_row, dict):
                    doc_count = list(doc_row.values())[0]
                else:
                    doc_count = doc_row[0]

                cur.execute("SELECT COUNT(*) FROM document_chunks;")
                chunk_row = cur.fetchone()
                if chunk_row is None:
                    chunk_count = 0
                elif isinstance(chunk_row, dict):
                    chunk_count = list(chunk_row.values())[0]
                else:
                    chunk_count = chunk_row[0]

        return {"status": "Connected", "documents": doc_count, "chunks": chunk_count, "error": None}
    except Exception as e:
        return {"status": "Error", "documents": 0, "chunks": 0, "error": str(e)}


# ==============================================================================
# Streamlit Web Application
# ==============================================================================
def run_streamlit_app():
    """Render the Streamlit RAG Dashboard."""
    st.set_page_config(
        page_title="pgvector-rag-engine | PostgreSQL pgvector + Groq",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS Styling
    st.markdown("""
        <style>
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            font-size: 1.05rem;
            color: #A0AEC0;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background-color: #1A202C;
            border: 1px solid #2D3748;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .stat-val {
            font-size: 1.8rem;
            font-weight: 700;
            color: #48BB78;
        }
        .stat-lbl {
            font-size: 0.85rem;
            color: #CBD5E0;
        }
        .source-box {
            background-color: #2D3748;
            border-left: 4px solid #3182CE;
            padding: 10px 14px;
            border-radius: 4px;
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-title">⚡ PostgreSQL 16 pgvector + Groq RAG Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Interactive Retrieval-Augmented Generation using Sentence Transformers & Groq Llama 3.3 70B</div>', unsafe_allow_html=True)

    # Sidebar Controls & System Status
    with st.sidebar:
        st.header("⚙️ System Status & Options")
        
        # Live Database Stats
        stats = get_db_stats()
        if stats["status"] == "Connected":
            st.success("🟢 **PostgreSQL EC2 Connected**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Documents", stats["documents"])
            with col_b:
                st.metric("Vector Chunks", stats["chunks"])
        else:
            st.error(f"🔴 **Database Offline**")
            st.caption(f"Error: {stats['error']}")
            st.info("Check `DATABASE_URL` in `.env` or EC2 Security Group rules.")

        st.divider()

        st.subheader("🎛️ RAG Parameters")
        top_k = st.slider("Top-K Retrieved Chunks", min_value=1, max_value=10, value=5)
        
        settings = get_settings()
        model_name = st.selectbox(
            "Groq LLM Model",
            options=["qwen/qwen3.6-27b", "openai/gpt-oss-20b", "groq/compound-mini", "allam-2-7b"],
            index=0
        )

        st.divider()
        st.caption("pgvector-rag-engine | Built with PostgreSQL 16, pgvector & Groq")

    # Main Tabs
    tab_chat, tab_ingest, tab_explorer = st.tabs([
        "💬 Interactive RAG Assistant",
        "📚 Document Management",
        "🔍 pgvector Search Explorer"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: RAG Chat Assistant
    # --------------------------------------------------------------------------
    with tab_chat:
        st.markdown("### Ask a Question to Your Knowledge Base")

        # Initialize Chat History
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {
                    "role": "assistant",
                    "content": "Hello! I am your RAG Assistant. Ask me anything about your ingested documents!",
                    "sources": []
                }
            ]

        # Sample Question Prompts
        st.markdown("**Sample Questions:**")
        col1, col2, col3 = st.columns(3)
        sample_q = None
        if col1.button("💡 What is PostgreSQL VACUUM?"):
            sample_q = "What is PostgreSQL VACUUM used for?"
        if col2.button("💡 How does pgvector search work?"):
            sample_q = "How does pgvector perform similarity search?"
        if col3.button("💡 Summarize the ingested docs"):
            sample_q = "Summarize the key topics covered in the document collection."

        # Display Chat History
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander("📚 View Retrieved Context Sources"):
                        for src in msg["sources"]:
                            st.markdown(
                                f"**File**: `{src['filename']}` | **Chunk**: `{src['chunk_index']}` | "
                                f"**Similarity Score**: `{src['similarity']:.4f}`"
                            )
                            st.caption(f"_{src.get('content_snippet', 'N/A')}_")
                            st.divider()

        # Chat Input
        user_input = st.chat_input("Type your question here...") or sample_q

        if user_input:
            # Display User Message
            st.session_state["messages"].append({"role": "user", "content": user_input, "sources": []})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate Assistant Response
            with st.chat_message("assistant"):
                with st.spinner("Searching pgvector database and generating response via Groq..."):
                    start_time = time.time()
                    try:
                        pipeline = get_pipeline(top_k=top_k, model_name=model_name)
                        result = pipeline.ask(user_input)
                        elapsed = time.time() - start_time

                        st.markdown(result["answer"])
                        st.caption(f"⏱️ Generated in {elapsed:.2f} seconds")

                        # Display Sources
                        if result["sources"]:
                            with st.expander("📚 View Retrieved Context Sources"):
                                for src in result["sources"]:
                                    st.markdown(
                                        f"**File**: `{src['filename']}` | **Chunk**: `{src['chunk_index']}` | "
                                        f"**Similarity**: `{src['similarity']:.4f}`"
                                    )

                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result["sources"]
                        })

                    except Exception as err:
                        st.error(f"Error executing RAG query: {err}")

    # --------------------------------------------------------------------------
    # TAB 2: Document Management & Ingestion
    # --------------------------------------------------------------------------
    with tab_ingest:
        st.markdown("### Document Ingestion & Storage")

        st.markdown("#### Option 1: Upload & Ingest New Document(s)")
        uploaded_files = st.file_uploader(
            "Select or drop `.txt`, `.pdf`, `.docx`, or `.md` files",
            type=["txt", "pdf", "docx", "md"],
            accept_multiple_files=True
        )

        if st.button("⚡ Ingest Uploaded File(s)"):
            if not uploaded_files:
                st.warning("⚠️ No files selected! Please browse or drag & drop a document file above first.")
            else:
                doc_dir = PROJECT_ROOT / "data" / "documents"
                doc_dir.mkdir(parents=True, exist_ok=True)
                
                with st.spinner("Processing, chunking & embedding uploaded document(s)..."):
                    try:
                        settings = get_settings()
                        database = Database(settings.database_url)
                        store = VectorStore(database)
                        embeddings = EmbeddingService(settings.embedding_model)

                        inserted_count = 0
                        skipped_count = 0

                        for uploaded_file in uploaded_files:
                            target_path = doc_dir / uploaded_file.name
                            with open(target_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            raw_text = load_document(target_path)
                            text = clean_text(raw_text)
                            if not text:
                                continue

                            # Check if document already exists in PostgreSQL before embedding
                            if store.is_document_exists(target_path.name, text):
                                skipped_count += 1
                                continue

                            chunks = split_text(text, settings.chunk_size, settings.chunk_overlap)
                            vectors = embeddings.embed_documents(chunks)
                            if store.add_document(target_path.name, text, chunks, vectors):
                                inserted_count += 1

                        if inserted_count > 0:
                            st.success(f"Successfully ingested {inserted_count} new document(s) into EC2 PostgreSQL!")
                        if skipped_count > 0:
                            st.info(f"Skipped {skipped_count} document(s) because they already exist in PostgreSQL database.")
                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")

        st.divider()

        st.markdown("#### Option 2: Ingest Existing Directory Documents (`data/documents/`)")
        doc_dir = PROJECT_ROOT / "data" / "documents"
        existing_files = [p for p in doc_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md", ".pdf", ".docx"}] if doc_dir.exists() else []

        st.caption(f"Currently **{len(existing_files)}** document file(s) found in `data/documents/` folder on disk.")

        col_dir1, col_dir2 = st.columns(2)
        with col_dir1:
            if st.button("📁 Ingest All Directory Files"):
                if not existing_files:
                    st.warning("No document files found in `data/documents/`. Generate sample docs or upload files first.")
                else:
                    with st.spinner(f"Checking and ingesting directory files into EC2 PostgreSQL..."):
                        try:
                            settings = get_settings()
                            database = Database(settings.database_url)
                            store = VectorStore(database)
                            embeddings = EmbeddingService(settings.embedding_model)

                            inserted_count = 0
                            skipped_count = 0

                            for path in existing_files:
                                raw_text = load_document(path)
                                text = clean_text(raw_text)
                                if not text:
                                    continue

                                # Check if document already exists in PostgreSQL before embedding
                                if store.is_document_exists(path.name, text):
                                    skipped_count += 1
                                    continue

                                chunks = split_text(text, settings.chunk_size, settings.chunk_overlap)
                                vectors = embeddings.embed_documents(chunks)
                                if store.add_document(path.name, text, chunks, vectors):
                                    inserted_count += 1

                            if inserted_count > 0:
                                st.success(f"Directory ingestion complete! Inserted {inserted_count} new document(s).")
                            if skipped_count > 0:
                                st.info(f"Skipped {skipped_count} existing document(s) (already in PostgreSQL).")
                        except Exception as e:
                            st.error(f"Directory ingestion failed: {e}")

        with col_dir2:
            if st.button("🎲 Generate 100 Sample Documents"):
                with st.spinner("Generating sample files..."):
                    try:
                        from scripts.generate_sample_docs import main as gen_sample
                        gen_sample()
                        st.success("Generated 100 sample documents in `data/documents/`.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sample generation failed: {e}")



    # --------------------------------------------------------------------------
    # TAB 3: Vector Store Playground
    # --------------------------------------------------------------------------
    with tab_explorer:
        st.markdown("### Inspect Raw Vector Similarity Search")
        st.caption("Test pgvector similarity search directly without invoking the Groq LLM.")

        query_text = st.text_input("Enter search query for vector retrieval:", "What is PostgreSQL VACUUM?")
        top_k_val = st.slider("Top K Results", 1, 10, 5, key="explorer_k")

        if st.button("🔍 Run Vector Search"):
            if query_text.strip():
                with st.spinner("Computing query embedding and searching pgvector..."):
                    try:
                        settings = get_settings()
                        database = Database(settings.database_url)
                        embeddings = EmbeddingService(settings.embedding_model)
                        vector_store = VectorStore(database)

                        query_vec = embeddings.embed_text(query_text)
                        results = vector_store.similarity_search(query_vec, top_k=top_k_val)

                        if results:
                            st.success(f"Found {len(results)} matching chunks.")
                            for idx, res in enumerate(results, 1):
                                st.markdown(f"#### Result #{idx}")
                                col_res1, col_res2 = st.columns(2)
                                with col_res1:
                                    st.write(f"**Filename:** `{res['filename']}`")
                                    st.write(f"**Chunk Index:** `{res['chunk_index']}`")
                                with col_res2:
                                    st.write(f"**Similarity Score:** `{res['similarity']:.4f}`")
                                    st.write(f"**Document ID:** `{res['document_id']}`")
                                
                                st.text_area("Chunk Content:", res["content"], height=120, key=f"chunk_txt_{idx}")
                                st.divider()
                        else:
                            st.warning("No matching vector results found.")
                    except Exception as e:
                        st.error(f"Vector search failed: {e}")




# ==============================================================================
# CLI Assistant (Fallback when run directly with `python main.py --cli`)
# ==============================================================================
def run_cli_app() -> None:
    """Start interactive command-line question-answer loop."""
    pipeline = get_pipeline()

    print("\n=== RAG Interactive Assistant ===")
    print("Type 'exit' or 'quit' to exit.\n")

    while True:
        try:
            question = input("Ask a question: ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Exiting RAG Assistant.")
                break

            if not question:
                continue

            result = pipeline.ask(question)

            print("\nANSWER:")
            print(result["answer"])

            print("\nSOURCES:")
            for source in result["sources"]:
                print(
                    f" - {source['filename']} | "
                    f"chunk={source['chunk_index']} | "
                    f"similarity={source['similarity']:.4f}"
                )
            print()
        except KeyboardInterrupt:
            print("\nExiting.")
            break


# ==============================================================================
# Main Entrypoint
# ==============================================================================
if __name__ == "__main__":
    # If invoked directly with `python main.py`, launch Streamlit unless `--cli` flag is provided
    if "--cli" in sys.argv:
        run_cli_app()
    elif HAS_STREAMLIT:
        # Check if already running inside Streamlit
        try:
            # pyrefly: ignore [missing-import]
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            ctx = get_script_run_ctx()
            if ctx is not None:
                run_streamlit_app()
            else:
                # Launch Streamlit server automatically
                print("Launching Streamlit Web UI...")
                subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
        except Exception:
            run_streamlit_app()
    else:
        run_cli_app()
