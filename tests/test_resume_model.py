"""RED: Resume model exists with correct columns, init_db creates resumes table."""
import pytest
from sqlalchemy import inspect, text


def test_resume_model_importable():
    from app.models.resume import Resume
    assert Resume.__tablename__ == "resumes"


def test_resume_model_columns():
    from app.models.resume import Resume
    mapper = inspect(Resume)
    col_names = {c.key for c in mapper.columns}
    assert "id" in col_names
    assert "name" in col_names
    assert "original_filename" in col_names
    assert "file_path" in col_names
    assert "tags" in col_names
    assert "version" in col_names
    assert "parsed_text" in col_names
    assert "is_deleted" in col_names
    assert "created_at" in col_names


def test_init_db_creates_resumes_table(engine):
    # init_db already ran via conftest (create_all); verify table exists
    inspector = inspect(engine)
    assert "resumes" in inspector.get_table_names()


def test_application_resume_fk_column(engine):
    inspector = inspect(engine)
    app_cols = {c["name"] for c in inspector.get_columns("applications")}
    assert "resume_id" in app_cols


def test_resume_crud(db):
    from app.models.resume import Resume
    r = Resume(
        name="My Resume",
        original_filename="resume.pdf",
        file_path="/storage/resumes/resume.pdf",
        version="v1",
        parsed_text="Software engineer with 5 years experience.",
    )
    db.add(r)
    db.flush()
    assert r.id is not None
    assert r.is_deleted is False
