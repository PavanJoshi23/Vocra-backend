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
def sample_app_with_resume(db_session):
    resume = Resume(
        name="My Resume",
        original_filename="resume.pdf",
        file_path="/tmp/resume.pdf",
        parsed_text="Python developer with 5 years experience in FastAPI Docker",
    )
    db_session.add(resume)
    db_session.flush()

    application = Application(
        company_name="Acme Corp",
        job_title="Senior Python Engineer",
        status=ApplicationStatus.APPLIED,
        job_description="We need a Python engineer with FastAPI, Docker, and AWS experience.",
        resume_id=resume.id,
    )
    db_session.add(application)
    db_session.flush()
    return application


_MOCK_OLLAMA_RESPONSE = json.dumps({
    "technical_topics": [{"topic": "FastAPI", "priority": "high", "why": "Core requirement"}],
    "behavioral_questions": ["Tell me about a challenging project."],
    "coding_topics": ["async/await", "REST APIs"],
    "study_roadmap": [{"week": 1, "focus": "AWS basics", "resources": ["aws.amazon.com"]}],
})


def test_generate_interview_prep_returns_200(client, sample_app_with_resume):
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": _MOCK_OLLAMA_RESPONSE}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        resp = client.post(
            "/api/interview/generate",
            json={"application_id": sample_app_with_resume.id},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "technical_topics" in data
    assert "behavioral_questions" in data
    assert "coding_topics" in data
    assert "study_roadmap" in data
    assert data["from_cache"] is False


def test_generate_returns_cached_on_second_call(client, sample_app_with_resume):
    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": _MOCK_OLLAMA_RESPONSE}
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        # First call — hits Ollama
        client.post(
            "/api/interview/generate",
            json={"application_id": sample_app_with_resume.id},
        )
        call_count_after_first = mock_client.post.call_count

        # Second call — should use cache
        resp2 = client.post(
            "/api/interview/generate",
            json={"application_id": sample_app_with_resume.id},
        )

    assert resp2.status_code == 200
    assert resp2.json()["from_cache"] is True
    # Ollama should NOT have been called again
    assert mock_client.post.call_count == call_count_after_first


def test_generate_returns_503_when_ollama_unavailable(client, db_session):
    import httpx
    # Use an application with a unique JD so it has no cached entry
    fresh_app = Application(
        company_name="503 Corp",
        job_title="Cloud Architect",
        status=ApplicationStatus.APPLIED,
        job_description="Unique JD for 503 test: kubernetes terraform helm grafana datadog",
    )
    db_session.add(fresh_app)
    db_session.flush()

    with patch("app.ai.ollama_client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_cls.return_value = mock_client

        resp = client.post(
            "/api/interview/generate",
            json={"application_id": fresh_app.id},
        )

    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()


def test_generate_404_for_missing_application(client):
    resp = client.post("/api/interview/generate", json={"application_id": 99999})
    assert resp.status_code == 404


def test_generate_400_for_application_without_jd(client, db_session):
    no_jd_app = Application(
        company_name="No JD Corp",
        job_title="Engineer",
        status=ApplicationStatus.APPLIED,
        job_description=None,
    )
    db_session.add(no_jd_app)
    db_session.flush()

    resp = client.post(
        "/api/interview/generate", json={"application_id": no_jd_app.id}
    )
    assert resp.status_code == 400
