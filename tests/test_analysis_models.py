import pytest
from sqlalchemy import inspect

from app.models.extracted_skill import ExtractedSkill
from app.models.match_result import MatchResult


def test_extracted_skill_table_columns(db):
    inspector = inspect(db.bind)
    cols = {c["name"] for c in inspector.get_columns("extracted_skills")}
    assert cols >= {"id", "source_type", "source_id", "skill_name", "skill_type", "importance_score", "created_at"}


def test_match_result_table_columns(db):
    inspector = inspect(db.bind)
    cols = {c["name"] for c in inspector.get_columns("match_results")}
    assert cols >= {"id", "application_id", "resume_id", "match_score", "matching_keywords", "missing_keywords", "recommendations", "created_at"}


def test_extracted_skill_create(db):
    skill = ExtractedSkill(
        source_type="resume",
        source_id=1,
        skill_name="Python",
        skill_type="languages",
        importance_score=0.9,
    )
    db.add(skill)
    db.flush()
    assert skill.id is not None
    assert skill.source_type == "resume"
    assert skill.skill_name == "Python"


def test_match_result_create(db):
    result = MatchResult(
        application_id=1,
        resume_id=1,
        match_score=78.5,
        matching_keywords='["Python", "React"]',
        missing_keywords='["Go"]',
        recommendations='[]',
    )
    db.add(result)
    db.flush()
    assert result.id is not None
    assert result.match_score == 78.5


def test_source_type_enum_values():
    valid = {"resume", "jd"}
    # Just verify the model accepts both values
    for st in valid:
        skill = ExtractedSkill(source_type=st, source_id=1, skill_name="X", skill_type="languages")
        assert skill.source_type == st
