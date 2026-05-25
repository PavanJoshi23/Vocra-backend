import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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
from app.models import ai_cache as _ac_mod  # noqa: F401
from app.models import interview_prep as _ip_mod  # noqa: F401
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
def sample_data(db_session):
    resume = Resume(
        name="My Resume",
        original_filename="resume.pdf",
        file_path="/tmp/resume.pdf",
        parsed_text="Built REST APIs using Python and Flask",
    )
    db_session.add(resume)
    db_session.flush()

    application = Application(
        company_name="TechCo",
        job_title="Backend Engineer",
        status=ApplicationStatus.APPLIED,
        job_description="We build FastAPI services with Docker and AWS.",
        resume_id=resume.id,
    )
    db_session.add(application)
    db_session.flush()
    return {"application": application, "resume": resume}


_MOCK_IMPROVE_RESPONSE = json.dumps({
    "original": "Built REST APIs using Python and Flask",
    "suggestion": "Designed and implemented high-performance REST APIs in Python with Flask, serving 50K daily requests",
    "changes": ["added quantification", "added 'Designed and implemented'"],
})


def test_improve_resume_returns_200(client, sample_data):
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": _MOCK_IMPROVE_RESPONSE}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        resp = client.post(
            "/api/analysis/improve-resume",
            json={
                "resume_id": sample_data["resume"].id,
                "application_id": sample_data["application"].id,
                "bullet_text": "Built REST APIs using Python and Flask",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "original" in data
    assert "suggestion" in data
    assert "changes" in data
    assert data["original"] == "Built REST APIs using Python and Flask"


def test_improve_resume_original_is_unchanged_input(client, sample_data):
    bullet = "Worked on databases and backend systems"
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": json.dumps({
            "original": bullet,
            "suggestion": "Optimized database queries reducing latency by 30%",
            "changes": ["added metric"],
        })}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        resp = client.post(
            "/api/analysis/improve-resume",
            json={
                "resume_id": sample_data["resume"].id,
                "application_id": sample_data["application"].id,
                "bullet_text": bullet,
            },
        )

    assert resp.status_code == 200
    assert resp.json()["original"] == bullet


def test_improve_resume_cached_on_second_call(client, sample_data):
    bullet = "Cached bullet for testing second call behavior unique xyz"
    mock_json = json.dumps({
        "original": bullet,
        "suggestion": "Improved version of the bullet",
        "changes": ["improved wording"],
    })
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": mock_json}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        # First call
        client.post(
            "/api/analysis/improve-resume",
            json={
                "resume_id": sample_data["resume"].id,
                "application_id": sample_data["application"].id,
                "bullet_text": bullet,
            },
        )
        first_call_count = mock_client.post.call_count

        # Second call — same bullet + application_id
        resp2 = client.post(
            "/api/analysis/improve-resume",
            json={
                "resume_id": sample_data["resume"].id,
                "application_id": sample_data["application"].id,
                "bullet_text": bullet,
            },
        )

    assert resp2.status_code == 200
    # Ollama should NOT be called again
    assert mock_client.post.call_count == first_call_count


def test_improve_resume_503_when_ollama_down(client, sample_data):
    import httpx
    # Use a unique bullet not cached by prior tests
    bullet = "503 test unique bullet never seen before abcde12345"
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cls.return_value = mock_client

        resp = client.post(
            "/api/analysis/improve-resume",
            json={
                "resume_id": sample_data["resume"].id,
                "application_id": sample_data["application"].id,
                "bullet_text": bullet,
            },
        )

    assert resp.status_code == 503


def test_improve_resume_422_missing_fields(client):
    resp = client.post("/api/analysis/improve-resume", json={})
    assert resp.status_code == 422
