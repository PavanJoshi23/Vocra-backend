import json

from sqlalchemy.orm import Session

from app.ai.cache import get_cached, make_hash, store_cached
from app.ai.ollama_client import generate
from app.ai.prompts.interview_prep import build_prompt, parse_response
from app.models.application import Application
from app.models.interview_prep import InterviewPrep
from app.models.resume import Resume
from app.services.matcher import match
from app.services.skill_extractor import extract_skills

_MODEL = "qwen2.5:1.5b"


async def generate_prep(db: Session, application_id: int) -> InterviewPrep:
    app = db.get(Application, application_id)
    if app is None or app.is_deleted:
        raise LookupError(f"Application {application_id} not found")

    jd_text = app.job_description or ""
    if not jd_text.strip():
        raise ValueError("Application has no job description")

    resume_text = ""
    if app.resume_id:
        resume = db.get(Resume, app.resume_id)
        if resume and not resume.is_deleted:
            resume_text = resume.parsed_text or ""

    jd_skills = [s.skill_name for s in extract_skills(jd_text) if s.skill_type != "experience"][:10]
    resume_skills = [s.skill_name for s in extract_skills(resume_text) if s.skill_type != "experience"] if resume_text else []

    match_result = match(resume_skills, jd_skills) if resume_skills else None
    strengths = match_result.matched[:5] if match_result else []
    missing = match_result.missing if match_result else jd_skills

    ctx = {
        "role": app.job_title,
        "company": app.company_name,
        "jd_skills": jd_skills,
        "resume_strengths": strengths,
        "missing_skills": missing,
    }
    prompt = build_prompt(ctx)
    prompt_hash = make_hash(prompt)

    cached_response = get_cached(db, prompt_hash)
    if cached_response:
        topics = parse_response(cached_response)
        return _upsert_record(db, application_id, topics, prompt_hash, from_cache=True)

    raw = await generate(_MODEL, prompt)
    topics = parse_response(raw)

    store_cached(db, prompt_hash=prompt_hash, cache_key=f"interview_{application_id}", response=raw)

    return _upsert_record(db, application_id, topics, prompt_hash, from_cache=False)


def _upsert_record(
    db: Session,
    application_id: int,
    topics: list[str],
    prompt_hash: str,
    from_cache: bool,
) -> InterviewPrep:
    existing = db.query(InterviewPrep).filter_by(application_id=application_id).first()
    if existing:
        existing.technical_topics = json.dumps(topics)
        existing.behavioral_questions = "[]"
        existing.coding_topics = "[]"
        existing.study_roadmap = "[]"
        existing.prompt_hash = prompt_hash
        existing.from_cache = from_cache
        db.flush()
        return existing

    record = InterviewPrep(
        application_id=application_id,
        technical_topics=json.dumps(topics),
        behavioral_questions="[]",
        coding_topics="[]",
        study_roadmap="[]",
        prompt_hash=prompt_hash,
        from_cache=from_cache,
    )
    db.add(record)
    db.flush()
    return record
