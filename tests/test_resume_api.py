"""RED → GREEN: Resume upload/list/detail/delete API endpoints."""
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.models import application as _app_model  # noqa: F401
from app.models import resume as _resume_model  # noqa: F401


# ---------------------------------------------------------------------------
# In-memory DB override — StaticPool shares one connection across all threads
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_client(tmp_path_factory):
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Give each test a writable storage dir
    storage = tmp_path_factory.mktemp("storage")
    import app.api.resumes as resumes_module
    resumes_module.RESUME_STORAGE = storage / "resumes"
    resumes_module.RESUME_STORAGE.mkdir(parents=True, exist_ok=True)

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _make_pdf_bytes():
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Software Engineer Python FastAPI experience.")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


def _make_docx_bytes():
    from docx import Document
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph("React developer Node.js skills.")
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_upload_pdf(test_client):
    pdf_bytes = _make_pdf_bytes()
    resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("my_resume.pdf", pdf_bytes, "application/pdf")},
        data={"name": "My Resume", "version": "v1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "My Resume"
    assert body["version"] == "v1"
    assert "id" in body
    assert body["parsed_text"] != ""


def test_upload_docx(test_client):
    docx_bytes = _make_docx_bytes()
    resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"name": "DOCX Resume"},
    )
    assert resp.status_code == 201
    assert resp.json()["parsed_text"] != ""


def test_upload_rejects_non_pdf_docx(test_client):
    resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("notes.txt", b"just text", "text/plain")},
        data={"name": "Bad Upload"},
    )
    assert resp.status_code == 422


def test_upload_rejects_oversized_file(test_client):
    big = b"x" * (11 * 1024 * 1024)  # 11 MB
    resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("big.pdf", big, "application/pdf")},
        data={"name": "Big"},
    )
    assert resp.status_code == 413


def test_list_resumes(test_client):
    resp = test_client.get("/api/resumes")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 2  # uploaded in earlier tests


def test_get_resume_detail(test_client):
    # upload one, then fetch it
    pdf_bytes = _make_pdf_bytes()
    upload_resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("detail.pdf", pdf_bytes, "application/pdf")},
        data={"name": "Detail Resume"},
    )
    resume_id = upload_resp.json()["id"]

    resp = test_client.get(f"/api/resumes/{resume_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == resume_id
    assert resp.json()["parsed_text"] != ""


def test_get_resume_not_found(test_client):
    resp = test_client.get("/api/resumes/99999")
    assert resp.status_code == 404


def test_delete_resume(test_client):
    pdf_bytes = _make_pdf_bytes()
    upload_resp = test_client.post(
        "/api/resumes/upload",
        files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
        data={"name": "Delete Me"},
    )
    resume_id = upload_resp.json()["id"]

    del_resp = test_client.delete(f"/api/resumes/{resume_id}")
    assert del_resp.status_code == 204

    # Soft-deleted: should 404 on re-fetch
    get_resp = test_client.get(f"/api/resumes/{resume_id}")
    assert get_resp.status_code == 404
