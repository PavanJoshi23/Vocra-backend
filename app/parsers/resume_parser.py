import re
import unicodedata
from pathlib import Path

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def extract_text(file_path: Path, mime_type: str) -> str:
    """Extract clean text from a PDF or DOCX file. Returns '' on any error."""
    try:
        if mime_type == PDF_MIME or str(file_path).lower().endswith(".pdf"):
            return _extract_pdf(file_path)
        if mime_type == DOCX_MIME or str(file_path).lower().endswith(".docx"):
            return _extract_docx(file_path)
        return ""
    except Exception:
        return ""


def _extract_pdf(file_path: Path) -> str:
    import fitz  # pymupdf

    doc = fitz.open(str(file_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return _normalize(" ".join(pages))


def _extract_docx(file_path: Path) -> str:
    from docx import Document

    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return _normalize("\n".join(paragraphs))


def _normalize(text: str) -> str:
    # Normalize unicode to NFC
    text = unicodedata.normalize("NFC", text)
    # Collapse multiple whitespace (spaces/tabs) to single space per line
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
