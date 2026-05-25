"""Analysis service: orchestrates skill extraction + matching + ATS scoring,
and persists results to match_results table (upsert).
"""

import json

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.match_result import MatchResult
from app.models.resume import Resume
from app.services.ats_scorer import ScoreBreakdown, compute_ats_score
from app.services.matcher import match
from app.services.skill_extractor import extract_skills


def run_match(db: Session, application_id: int, resume_id: int) -> MatchResult:
    app = db.get(Application, application_id)
    if app is None or app.is_deleted:
        raise LookupError(f"Application {application_id} not found")

    resume = db.get(Resume, resume_id)
    if resume is None or resume.is_deleted:
        raise LookupError(f"Resume {resume_id} not found")

    jd_text = app.job_description or ""
    if not jd_text.strip():
        raise ValueError("Application has no job description — cannot run analysis")

    resume_text = resume.parsed_text or ""

    # Extract skills from both texts
    jd_skills = [s.skill_name for s in extract_skills(jd_text) if s.skill_type != "experience"]
    resume_skills = [s.skill_name for s in extract_skills(resume_text) if s.skill_type != "experience"]

    # Three-layer match
    match_result = match(resume_skills, jd_skills)

    # ATS score
    breakdown: ScoreBreakdown = compute_ats_score(resume_text, jd_text)

    # Upsert into match_results
    existing = (
        db.query(MatchResult)
        .filter_by(application_id=application_id, resume_id=resume_id)
        .first()
    )

    score_breakdown_json = json.dumps({
        "skills": breakdown.skills,
        "experience": breakdown.experience,
        "keyword_coverage": breakdown.keyword_coverage,
        "education": breakdown.education,
    })

    if existing:
        existing.match_score = breakdown.total
        existing.matching_keywords = json.dumps(match_result.matched)
        existing.missing_keywords = json.dumps(match_result.missing)
        existing.recommendations = json.dumps([])
        existing.score_breakdown = score_breakdown_json
        db.flush()
        return existing
    else:
        record = MatchResult(
            application_id=application_id,
            resume_id=resume_id,
            match_score=breakdown.total,
            matching_keywords=json.dumps(match_result.matched),
            missing_keywords=json.dumps(match_result.missing),
            recommendations=json.dumps([]),
            score_breakdown=score_breakdown_json,
        )
        db.add(record)
        db.flush()
        return record


def get_latest_result(db: Session, application_id: int) -> MatchResult | None:
    return (
        db.query(MatchResult)
        .filter_by(application_id=application_id)
        .order_by(MatchResult.created_at.desc())
        .first()
    )
