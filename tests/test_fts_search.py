"""
Tests for SQLite FTS5 full-text search in applications.
RED: fails before FTS5 table + triggers + service update.
GREEN: passes once implemented.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models import application  # noqa: F401
from app.models import resume  # noqa: F401
from app.models import extracted_skill  # noqa: F401
from app.models import match_result  # noqa: F401
from app.models import ai_cache  # noqa: F401
from app.models import interview_prep  # noqa: F401
from app.models.application import Application, ApplicationStatus
from app.services.applications import list_applications
from app.services.fts import setup_fts


@pytest.fixture
def fts_engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    setup_fts(eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def fts_db(fts_engine):
    Session = sessionmaker(bind=fts_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def _create_app(db, company, title, notes="", jd=""):
    app = Application(
        company_name=company,
        job_title=title,
        notes=notes,
        job_description=jd,
        status=ApplicationStatus.APPLIED,
        is_deleted=False,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def test_fts_table_exists(fts_engine):
    with fts_engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='applications_fts'")
        )
        assert result.fetchone() is not None


def test_fts_insert_trigger_syncs(fts_engine, fts_db):
    _create_app(fts_db, "Acme Corp", "Python Developer")
    with fts_engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM applications_fts WHERE applications_fts MATCH 'Acme'")
        )
        assert result.scalar() == 1


def test_fts_delete_trigger_removes_entry(fts_engine, fts_db):
    app = _create_app(fts_db, "DeleteCo", "Engineer")
    app.is_deleted = True
    fts_db.commit()
    with fts_engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM applications_fts WHERE applications_fts MATCH 'DeleteCo'")
        )
        assert result.scalar() == 0


def test_fts_search_via_list_applications(fts_db):
    _create_app(fts_db, "Skynet Inc", "ML Engineer", jd="machine learning python tensorflow")
    _create_app(fts_db, "Initech", "Java Dev", jd="java spring microservices")

    results, total = list_applications(fts_db, search="tensorflow")
    assert total == 1
    assert results[0].company_name == "Skynet Inc"


def test_fts_search_no_match_returns_empty(fts_db):
    _create_app(fts_db, "Globex", "Sales Rep")
    results, total = list_applications(fts_db, search="quantumcomputing")
    assert total == 0
    assert results == []


def test_fts_phrase_search(fts_db):
    _create_app(fts_db, "PhraseTest Co", "Dev", jd="distributed systems engineer")
    _create_app(fts_db, "Other Co", "Dev", jd="python web developer")
    results, total = list_applications(fts_db, search='"distributed systems"')
    assert total == 1
    assert results[0].company_name == "PhraseTest Co"
