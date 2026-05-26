"""Tests for GET /api/applications/export?format=json|csv"""
import csv
import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.database.session import Base
from app.models import application, resume, extracted_skill, match_result, ai_cache, interview_prep  # noqa: F401
from app.models.application import Application, ApplicationStatus


@pytest.fixture(scope="module")
def export_engine():
    # StaticPool reuses a single connection so all sessions share the same in-memory DB
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def export_db(export_engine):
    Session = sessionmaker(bind=export_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(export_engine):
    def override_get_db():
        Session = sessionmaker(bind=export_engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def seed_applications(export_db):
    from sqlalchemy import delete as sa_delete
    from app.models.application import Application as AppModel

    apps = [
        Application(
            company_name="Acme Corp",
            job_title="Python Developer",
            status=ApplicationStatus.APPLIED,
            notes="Great company",
            salary_min=80000,
            salary_max=100000,
            is_deleted=False,
        ),
        Application(
            company_name="Beta Inc",
            job_title="Backend Engineer",
            status=ApplicationStatus.INTERVIEW,
            notes=None,
            is_deleted=False,
        ),
        Application(
            company_name="Deleted Co",
            job_title="Dev",
            status=ApplicationStatus.REJECTED,
            is_deleted=True,
        ),
    ]
    for a in apps:
        export_db.add(a)
    export_db.commit()
    yield
    export_db.execute(sa_delete(AppModel))
    export_db.commit()


def test_export_json_returns_200(client):
    resp = client.get("/api/applications/export?format=json")
    assert resp.status_code == 200


def test_export_json_content_type(client):
    resp = client.get("/api/applications/export?format=json")
    assert "application/json" in resp.headers["content-type"]


def test_export_json_excludes_deleted(client):
    resp = client.get("/api/applications/export?format=json")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    companies = [a["company_name"] for a in data]
    assert "Deleted Co" not in companies


def test_export_json_contains_all_fields(client):
    resp = client.get("/api/applications/export?format=json")
    data = resp.json()
    first = data[0]
    assert "id" in first
    assert "company_name" in first
    assert "job_title" in first
    assert "status" in first
    assert "created_at" in first


def test_export_csv_returns_200(client):
    resp = client.get("/api/applications/export?format=csv")
    assert resp.status_code == 200


def test_export_csv_content_type(client):
    resp = client.get("/api/applications/export?format=csv")
    assert "text/csv" in resp.headers["content-type"]


def test_export_csv_excludes_deleted(client):
    resp = client.get("/api/applications/export?format=csv")
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    assert len(rows) == 2
    companies = [r["company_name"] for r in rows]
    assert "Deleted Co" not in companies


def test_export_csv_has_header_row(client):
    resp = client.get("/api/applications/export?format=csv")
    lines = resp.text.strip().splitlines()
    assert len(lines) >= 2  # header + at least 1 data row
    header = lines[0]
    assert "company_name" in header
    assert "job_title" in header
    assert "status" in header


def test_export_invalid_format_returns_422(client):
    resp = client.get("/api/applications/export?format=xlsx")
    assert resp.status_code == 422
