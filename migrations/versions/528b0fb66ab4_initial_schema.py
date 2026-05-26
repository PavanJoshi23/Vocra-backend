"""initial_schema

Revision ID: 528b0fb66ab4
Revises:
Create Date: 2026-05-26 07:19:24.249751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '528b0fb66ab4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=64), nullable=True),
        sa.Column('parsed_text', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('job_link', sa.String(length=2048), nullable=True),
        sa.Column('application_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('wishlist', 'applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn', name='applicationstatus'), nullable=False),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'extracted_skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_type', sa.String(length=16), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=255), nullable=False),
        sa.Column('skill_type', sa.String(length=64), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'match_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('matching_keywords', sa.Text(), nullable=True),
        sa.Column('missing_keywords', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('score_breakdown', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ai_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('prompt_hash', sa.String(length=64), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
    )
    op.create_index('ix_ai_cache_cache_key', 'ai_cache', ['cache_key'], unique=True)
    op.create_index('ix_ai_cache_prompt_hash', 'ai_cache', ['prompt_hash'])

    op.create_table(
        'interview_prep',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('technical_topics', sa.Text(), nullable=True),
        sa.Column('behavioral_questions', sa.Text(), nullable=True),
        sa.Column('coding_topics', sa.Text(), nullable=True),
        sa.Column('study_roadmap', sa.Text(), nullable=True),
        sa.Column('prompt_hash', sa.String(length=64), nullable=False),
        sa.Column('from_cache', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_interview_prep_application_id', 'interview_prep', ['application_id'])


def downgrade() -> None:
    op.drop_index('ix_interview_prep_application_id', table_name='interview_prep')
    op.drop_table('interview_prep')
    op.drop_index('ix_ai_cache_prompt_hash', table_name='ai_cache')
    op.drop_index('ix_ai_cache_cache_key', table_name='ai_cache')
    op.drop_table('ai_cache')
    op.drop_table('match_results')
    op.drop_table('extracted_skills')
    op.drop_table('applications')
    op.drop_table('resumes')
