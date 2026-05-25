"""RED → GREEN: resume_parser.extract_text() for PDF, DOCX, corrupted file."""
import io
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixture helpers — build minimal PDF and DOCX in-memory without external files
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    import fitz
    tmp = tmp_path_factory.mktemp("fixtures")
    path = tmp / "resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Software Engineer with Python and FastAPI experience.")
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture(scope="module")
def sample_docx(tmp_path_factory):
    from docx import Document
    tmp = tmp_path_factory.mktemp("fixtures")
    path = tmp / "resume.docx"
    doc = Document()
    doc.add_paragraph("Full Stack Developer skilled in React and Node.js.")
    doc.save(str(path))
    return path


@pytest.fixture(scope="module")
def corrupted_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("fixtures")
    path = tmp / "bad.pdf"
    path.write_bytes(b"this is not a valid pdf")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_extract_text_from_pdf(sample_pdf):
    from app.parsers.resume_parser import extract_text
    text = extract_text(sample_pdf, "application/pdf")
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Python" in text or "FastAPI" in text


def test_extract_text_from_docx(sample_docx):
    from app.parsers.resume_parser import extract_text
    text = extract_text(sample_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert isinstance(text, str)
    assert "React" in text or "Node" in text


def test_extract_text_corrupted_returns_empty(corrupted_file):
    from app.parsers.resume_parser import extract_text
    text = extract_text(corrupted_file, "application/pdf")
    assert text == ""


def test_extract_text_normalizes_whitespace(sample_pdf):
    from app.parsers.resume_parser import extract_text
    text = extract_text(sample_pdf, "application/pdf")
    assert "  " not in text  # no double spaces
    assert not text.startswith("\n")
    assert not text.endswith("\n")


def test_extract_text_unknown_type_returns_empty(tmp_path):
    from app.parsers.resume_parser import extract_text
    p = tmp_path / "file.xyz"
    p.write_bytes(b"some bytes")
    text = extract_text(p, "application/octet-stream")
    assert text == ""
