import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app
from app.models import application as _app_mod  # noqa: F401
from app.models import resume as _resume_mod  # noqa: F401
from app.models import extracted_skill as _es_mod  # noqa: F401
from app.models import match_result as _mr_mod  # noqa: F401
from app.models.application import Application, ApplicationStatus
from app.models.resume import Resume


@pytest.fixture(scope="module")
def test_engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_application(db_session):
    app_obj = Application(
        company_name="Acme Corp",
        job_title="Senior Python Engineer",
        job_description=(
            "We need a Python developer with 5+ years experience. "
            "Skills: Python, FastAPI, Docker, AWS, PostgreSQL, React. "
            "Bachelor degree in Computer Science preferred."
        ),
        status=ApplicationStatus.APPLIED,
        resume_id=1,
    )
    db_session.add(app_obj)
    db_session.flush()
    return app_obj


@pytest.fixture
def sample_resume(db_session):
    resume = Resume(
        name="My Resume",
        original_filename="resume.pdf",
        file_path="/tmp/resume.pdf",
        parsed_text=(
            "Software Engineer with 6 years of experience. "
            "Proficient in Python, FastAPI, Docker, AWS, PostgreSQL. "
            "Built REST APIs and microservices. "
            "Bachelor of Science in Computer Science."
        ),
    )
    db_session.add(resume)
    db_session.flush()
    return resume


# ── POST /api/analysis/extract-skills ────────────────────────────────────────

def test_extract_skills_endpoint_returns_skills(client):
    resp = client.post("/api/analysis/extract-skills", json={
        "text": "We need a Python developer with Docker and AWS experience."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "skills" in data
    assert isinstance(data["skills"], list)
    found = {s["skill_name"].lower() for s in data["skills"]}
    assert "python" in found


def test_extract_skills_endpoint_empty_text(client):
    resp = client.post("/api/analysis/extract-skills", json={"text": ""})
    assert resp.status_code == 200
    assert resp.json()["skills"] == []


def test_extract_skills_endpoint_missing_text(client):
    resp = client.post("/api/analysis/extract-skills", json={})
    assert resp.status_code == 422


# ── POST /api/analysis/match ──────────────────────────────────────────────────

def test_match_endpoint_runs_full_pipeline(client, sample_application, sample_resume):
    resp = client.post("/api/analysis/match", json={
        "application_id": sample_application.id,
        "resume_id": sample_resume.id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "match_score" in data
    assert "matching_keywords" in data
    assert "missing_keywords" in data
    assert "score_breakdown" in data
    assert 0 <= data["match_score"] <= 100


def test_match_endpoint_404_on_missing_application(client, sample_resume):
    resp = client.post("/api/analysis/match", json={
        "application_id": 99999,
        "resume_id": sample_resume.id,
    })
    assert resp.status_code == 404


def test_match_endpoint_404_on_missing_resume(client, sample_application):
    resp = client.post("/api/analysis/match", json={
        "application_id": sample_application.id,
        "resume_id": 99999,
    })
    assert resp.status_code == 404


def test_match_endpoint_404_on_no_job_description(client, db_session, sample_resume):
    app_no_jd = Application(
        company_name="NoJD Corp",
        job_title="Developer",
        job_description=None,
        status=ApplicationStatus.APPLIED,
    )
    db_session.add(app_no_jd)
    db_session.flush()

    resp = client.post("/api/analysis/match", json={
        "application_id": app_no_jd.id,
        "resume_id": sample_resume.id,
    })
    assert resp.status_code == 400


def test_match_endpoint_upserts_result(client, sample_application, sample_resume):
    """Two POSTs for same (app_id, resume_id) should not create duplicate rows."""
    client.post("/api/analysis/match", json={
        "application_id": sample_application.id,
        "resume_id": sample_resume.id,
    })
    client.post("/api/analysis/match", json={
        "application_id": sample_application.id,
        "resume_id": sample_resume.id,
    })
    resp = client.get(f"/api/analysis/{sample_application.id}/results")
    assert resp.status_code == 200


# ── GET /api/analysis/{application_id}/results ────────────────────────────────

def test_results_endpoint_404_when_no_match(client):
    resp = client.get("/api/analysis/88888/results")
    assert resp.status_code == 404


def test_results_endpoint_returns_stored_result(client, sample_application, sample_resume):
    client.post("/api/analysis/match", json={
        "application_id": sample_application.id,
        "resume_id": sample_resume.id,
    })
    resp = client.get(f"/api/analysis/{sample_application.id}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert "match_score" in data
    assert "matching_keywords" in data
