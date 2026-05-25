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
from app.models import ai_cache as _ac_mod  # noqa: F401
from app.models import interview_prep as _ip_mod  # noqa: F401
from app.models.application import Application, ApplicationStatus
from app.models.extracted_skill import ExtractedSkill


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
def seeded_db(db_session):
    apps = [
        Application(company_name="Acme", job_title="Engineer", status=ApplicationStatus.APPLIED),
        Application(company_name="Beta", job_title="Developer", status=ApplicationStatus.INTERVIEW),
        Application(company_name="Gamma", job_title="Lead", status=ApplicationStatus.OFFER),
        Application(company_name="Delta", job_title="Analyst", status=ApplicationStatus.REJECTED),
        Application(company_name="Epsilon", job_title="Manager", status=ApplicationStatus.WISHLIST),
    ]
    for a in apps:
        db_session.add(a)

    skills = [
        ExtractedSkill(source_type="jd", source_id=1, skill_name="Python", skill_type="language"),
        ExtractedSkill(source_type="jd", source_id=2, skill_name="Python", skill_type="language"),
        ExtractedSkill(source_type="jd", source_id=3, skill_name="Docker", skill_type="tool"),
        ExtractedSkill(source_type="resume", source_id=1, skill_name="JavaScript", skill_type="language"),
    ]
    for s in skills:
        db_session.add(s)

    db_session.flush()
    return apps


# ── GET /api/dashboard/summary ────────────────────────────────────────────────

def test_dashboard_returns_200(client, seeded_db):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200


def test_dashboard_has_all_top_level_keys(client, seeded_db):
    data = client.get("/api/dashboard/summary").json()
    assert "totals" in data
    assert "rates" in data
    assert "monthly_trend" in data
    assert "status_distribution" in data
    assert "skill_demand" in data


def test_dashboard_totals_structure(client, seeded_db):
    totals = client.get("/api/dashboard/summary").json()["totals"]
    assert "total" in totals
    assert "applied" in totals
    assert "interviewing" in totals
    assert "offers" in totals
    assert "rejected" in totals
    assert "pending_followups" in totals


def test_dashboard_totals_count_all_non_deleted(client, seeded_db):
    totals = client.get("/api/dashboard/summary").json()["totals"]
    assert totals["total"] == 5


def test_dashboard_totals_count_interviewing(client, seeded_db):
    totals = client.get("/api/dashboard/summary").json()["totals"]
    assert totals["interviewing"] == 1  # INTERVIEW status


def test_dashboard_totals_count_offers(client, seeded_db):
    totals = client.get("/api/dashboard/summary").json()["totals"]
    assert totals["offers"] == 1


def test_dashboard_totals_count_rejected(client, seeded_db):
    totals = client.get("/api/dashboard/summary").json()["totals"]
    assert totals["rejected"] == 1


def test_dashboard_rates_are_valid_floats(client, seeded_db):
    rates = client.get("/api/dashboard/summary").json()["rates"]
    assert isinstance(rates["interview_rate"], float)
    assert isinstance(rates["offer_rate"], float)
    assert isinstance(rates["rejection_rate"], float)
    assert 0.0 <= rates["interview_rate"] <= 1.0
    assert 0.0 <= rates["offer_rate"] <= 1.0
    assert 0.0 <= rates["rejection_rate"] <= 1.0


def test_dashboard_monthly_trend_is_list_of_dicts(client, seeded_db):
    trend = client.get("/api/dashboard/summary").json()["monthly_trend"]
    assert isinstance(trend, list)
    if trend:
        assert "month" in trend[0]
        assert "count" in trend[0]


def test_dashboard_monthly_trend_covers_6_months(client, seeded_db):
    trend = client.get("/api/dashboard/summary").json()["monthly_trend"]
    assert len(trend) == 6


def test_dashboard_status_distribution_is_list(client, seeded_db):
    dist = client.get("/api/dashboard/summary").json()["status_distribution"]
    assert isinstance(dist, list)
    assert len(dist) > 0
    assert "status" in dist[0]
    assert "count" in dist[0]


def test_dashboard_skill_demand_uses_jd_skills_only(client, seeded_db):
    skills = client.get("/api/dashboard/summary").json()["skill_demand"]
    skill_names = [s["skill"] for s in skills]
    assert "Python" in skill_names
    assert "JavaScript" not in skill_names  # resume-sourced, not JD


def test_dashboard_skill_demand_ordered_by_count_desc(client, seeded_db):
    skills = client.get("/api/dashboard/summary").json()["skill_demand"]
    if len(skills) >= 2:
        counts = [s["count"] for s in skills]
        assert counts == sorted(counts, reverse=True)


def test_dashboard_skill_demand_python_count_is_2(client, seeded_db):
    skills = client.get("/api/dashboard/summary").json()["skill_demand"]
    python_entry = next((s for s in skills if s["skill"] == "Python"), None)
    assert python_entry is not None
    assert python_entry["count"] == 2


def test_dashboard_empty_database(client):
    """Empty DB still returns valid structure with zeros."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["totals"]["total"] == 0
    assert data["rates"]["interview_rate"] == 0.0
    assert data["rates"]["offer_rate"] == 0.0
    assert len(data["monthly_trend"]) == 6
    assert data["skill_demand"] == []
