"""add_fts5_virtual_table

Revision ID: 9f0185bed959
Revises: 528b0fb66ab4
Create Date: 2026-05-26 07:24:02.925397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9f0185bed959'
down_revision: Union[str, Sequence[str], None] = '528b0fb66ab4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS applications_fts USING fts5(
            company_name,
            job_title,
            notes,
            job_description,
            content='applications',
            content_rowid='id'
        )
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS applications_ai AFTER INSERT ON applications BEGIN
            INSERT INTO applications_fts(rowid, company_name, job_title, notes, job_description)
            VALUES (new.id, new.company_name, new.job_title,
                    COALESCE(new.notes,''), COALESCE(new.job_description,''));
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS applications_au AFTER UPDATE ON applications BEGIN
            INSERT INTO applications_fts(applications_fts, rowid, company_name, job_title, notes, job_description)
            VALUES ('delete', old.id, old.company_name, old.job_title,
                    COALESCE(old.notes,''), COALESCE(old.job_description,''));
            INSERT INTO applications_fts(rowid, company_name, job_title, notes, job_description)
            SELECT new.id, new.company_name, new.job_title,
                   COALESCE(new.notes,''), COALESCE(new.job_description,'')
            WHERE new.is_deleted = 0;
        END
    """)
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS applications_ad AFTER DELETE ON applications BEGIN
            INSERT INTO applications_fts(applications_fts, rowid, company_name, job_title, notes, job_description)
            VALUES ('delete', old.id, old.company_name, old.job_title,
                    COALESCE(old.notes,''), COALESCE(old.job_description,''));
        END
    """)
    # Backfill existing rows
    op.execute("""
        INSERT INTO applications_fts(rowid, company_name, job_title, notes, job_description)
        SELECT id, company_name, job_title,
               COALESCE(notes,''), COALESCE(job_description,'')
        FROM applications
        WHERE is_deleted = 0
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS applications_ad")
    op.execute("DROP TRIGGER IF EXISTS applications_au")
    op.execute("DROP TRIGGER IF EXISTS applications_ai")
    op.execute("DROP TABLE IF EXISTS applications_fts")
