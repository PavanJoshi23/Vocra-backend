"""
SQLite FTS5 setup for applications full-text search.

setup_fts(engine) creates the FTS5 virtual table and INSERT/UPDATE/DELETE
triggers. Call once at startup after init_db().
"""
from sqlalchemy import Engine, text

_CREATE_FTS_TABLE = """
    CREATE VIRTUAL TABLE IF NOT EXISTS applications_fts USING fts5(
        company_name,
        job_title,
        notes,
        job_description,
        content='applications',
        content_rowid='id'
    )
"""

_CREATE_TRIGGER_AI = """
    CREATE TRIGGER IF NOT EXISTS applications_ai AFTER INSERT ON applications BEGIN
        INSERT INTO applications_fts(rowid, company_name, job_title, notes, job_description)
        VALUES (
            new.id,
            new.company_name,
            new.job_title,
            COALESCE(new.notes, ''),
            COALESCE(new.job_description, '')
        );
    END
"""

_CREATE_TRIGGER_AU = """
    CREATE TRIGGER IF NOT EXISTS applications_au AFTER UPDATE ON applications BEGIN
        INSERT INTO applications_fts(applications_fts, rowid, company_name, job_title, notes, job_description)
        VALUES (
            'delete',
            old.id,
            old.company_name,
            old.job_title,
            COALESCE(old.notes, ''),
            COALESCE(old.job_description, '')
        );
        INSERT INTO applications_fts(rowid, company_name, job_title, notes, job_description)
        SELECT
            new.id,
            new.company_name,
            new.job_title,
            COALESCE(new.notes, ''),
            COALESCE(new.job_description, '')
        WHERE new.is_deleted = 0;
    END
"""

_CREATE_TRIGGER_AD = """
    CREATE TRIGGER IF NOT EXISTS applications_ad AFTER DELETE ON applications BEGIN
        INSERT INTO applications_fts(applications_fts, rowid, company_name, job_title, notes, job_description)
        VALUES (
            'delete',
            old.id,
            old.company_name,
            old.job_title,
            COALESCE(old.notes, ''),
            COALESCE(old.job_description, '')
        );
    END
"""


def setup_fts(engine: Engine) -> None:
    """Create FTS5 virtual table and sync triggers if they do not already exist."""
    with engine.connect() as conn:
        for ddl in [_CREATE_FTS_TABLE, _CREATE_TRIGGER_AI, _CREATE_TRIGGER_AU, _CREATE_TRIGGER_AD]:
            conn.execute(text(ddl))
        conn.commit()
