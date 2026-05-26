"""
Test that alembic migrations can run against a fresh SQLite database.
RED: fails before migrations exist; GREEN: passes once initial migration is created.
"""
import os
import tempfile
import pytest
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect, text


BACKEND_DIR = Path(__file__).resolve().parents[1]


def make_alembic_cfg(db_path: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return cfg


def test_upgrade_head_creates_all_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        cfg = make_alembic_cfg(db_path)
        command.upgrade(cfg, "head")

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "applications" in tables
        assert "resumes" in tables
        assert "extracted_skills" in tables
        assert "match_results" in tables
        assert "ai_cache" in tables
        assert "interview_prep" in tables


def test_downgrade_base_removes_all_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        cfg = make_alembic_cfg(db_path)
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "applications" not in tables
        assert "resumes" not in tables
