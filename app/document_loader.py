"""Document loading for TXT, Markdown, PDF, and DOCX files."""

from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument


def load_document(path: Path) -> str:
    """Extract plain text from a supported document."""
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix == ".docx":
        doc = DocxDocument(str(path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {suffix}")


def clean_text(text: str) -> str:
    """Normalize whitespace while keeping paragraph boundaries useful."""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
