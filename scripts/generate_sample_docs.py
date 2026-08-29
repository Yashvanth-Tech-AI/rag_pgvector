import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT = PROJECT_ROOT / "data" / "documents"
OUTPUT.mkdir(parents=True, exist_ok=True)


topics = [
    ("PostgreSQL Backup", "PostgreSQL backups protect database data and support recovery after failures. A backup strategy commonly combines logical or physical backups with WAL archiving."),
    ("PostgreSQL Vacuum", "VACUUM removes obsolete row versions and helps PostgreSQL control table bloat. ANALYZE updates planner statistics so the optimizer can make better decisions."),
    ("PostgreSQL Indexes", "B-tree indexes are useful for equality and range predicates. Indexes improve reads but add storage and write overhead, so they should be created for useful access patterns."),
    ("PostgreSQL Replication", "Streaming replication continuously sends WAL records from a primary PostgreSQL server to a standby. Replication supports high availability and read scaling."),
    ("PostgreSQL Connection Pooling", "Connection pooling reuses database connections and can reduce connection setup overhead. Pool sizes should be chosen carefully because every active PostgreSQL connection consumes resources."),
    ("AWS EC2", "Amazon EC2 provides resizable compute capacity. An EC2 instance is selected using CPU, memory, storage, network, and workload requirements."),
    ("AWS S3", "Amazon S3 is object storage designed for durable storage of files and objects. Applications commonly use S3 for backups, data lakes, logs, and static assets."),
    ("AWS RDS", "Amazon RDS is a managed relational database service. It automates several operational tasks such as backups, patching, and infrastructure provisioning."),
    ("AWS CloudWatch", "Amazon CloudWatch collects metrics, logs, and alarms for AWS resources and applications. It can be used to monitor CPU utilization, storage, latency, and application events."),
    ("RAG Architecture", "Retrieval-Augmented Generation combines information retrieval with language generation. A retriever finds relevant knowledge and an LLM uses that knowledge to produce a grounded answer."),
]

for i in range(1, 101):
    topic, text = topics[(i - 1) % len(topics)]
    content = f"""Document {i}
Topic: {topic}

{text}

Prototype reference:
This document is synthetic sample content created for demonstrating document ingestion,
chunking, embeddings, PostgreSQL pgvector retrieval, and Groq-powered RAG.
"""
    (OUTPUT / f"sample_{i:03d}.txt").write_text(content, encoding="utf-8")

print("Generated 100 sample documents in data/documents/")
