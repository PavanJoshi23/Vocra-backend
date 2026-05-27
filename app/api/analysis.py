import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.cache import get_cached, make_hash, store_cached
from app.ai.ollama_client import OllamaTimeoutError, OllamaUnavailableError
from app.ai.prompts.resume_improve import build_improve_prompt, parse_improve_response
from app.ai.ollama_client import generate as ollama_generate
from app.database import get_db
from app.models.application import Application
from app.schemas.analysis import (
    ExtractSkillsRequest,
    ExtractSkillsResponse,
    ExtractedSkillItem,
    ImproveResumeRequest,
    ImproveResumeResponse,
    MatchRequest,
    MatchResponse,
    ScoreBreakdownSchema,
)
from app.services import analysis as analysis_service
from app.services.skill_extractor import extract_skills

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/extract-skills", response_model=ExtractSkillsResponse)
def extract_skills_endpoint(body: ExtractSkillsRequest) -> ExtractSkillsResponse:
    skills = extract_skills(body.text)
    return ExtractSkillsResponse(
        skills=[
            ExtractedSkillItem(
                skill_name=s.skill_name,
                skill_type=s.skill_type,
                importance_score=s.importance_score,
            )
            for s in skills
        ]
    )


@router.post("/match", response_model=MatchResponse)
def run_match(body: MatchRequest, db: Session = Depends(get_db)) -> MatchResponse:
    try:
        record = analysis_service.run_match(db, body.application_id, body.resume_id)
        db.commit()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    breakdown_raw = json.loads(record.score_breakdown or "{}")
    return MatchResponse(
        id=record.id,
        application_id=record.application_id,
        resume_id=record.resume_id,
        match_score=record.match_score,
        matching_keywords=json.loads(record.matching_keywords or "[]"),
        missing_keywords=json.loads(record.missing_keywords or "[]"),
        score_breakdown=ScoreBreakdownSchema(
            skills=breakdown_raw.get("skills", 0),
            experience=breakdown_raw.get("experience", 0),
            keyword_coverage=breakdown_raw.get("keyword_coverage", 0),
            education=breakdown_raw.get("education", 0),
        ),
        created_at=record.created_at,
    )


@router.post("/improve-resume", response_model=ImproveResumeResponse)
async def improve_resume(
    body: ImproveResumeRequest, db: Session = Depends(get_db)
) -> ImproveResumeResponse:
    application = db.get(Application, body.application_id)
    if application is None or application.is_deleted:
        raise HTTPException(status_code=404, detail=f"Application {body.application_id} not found")

    jd_text = application.job_description or ""
    jd_keywords = [s.skill_name for s in extract_skills(jd_text) if s.skill_type != "experience"][:10]

    prompt = build_improve_prompt(
        bullet_text=body.bullet_text,
        job_title=application.job_title,
        company=application.company_name,
        jd_keywords=jd_keywords,
    )
    cache_key = f"improve_{body.application_id}_{make_hash(body.bullet_text)}"
    prompt_hash = make_hash(prompt)

    cached = get_cached(db, prompt_hash)
    if cached:
        parsed = parse_improve_response(cached, body.bullet_text)
        return ImproveResumeResponse(**parsed)

    try:
        raw = await ollama_generate("qwen2.5:1.5b", prompt)
    except (OllamaUnavailableError, OllamaTimeoutError) as exc:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {exc}")

    store_cached(db, prompt_hash=prompt_hash, cache_key=cache_key, response=raw)
    db.commit()

    parsed = parse_improve_response(raw, body.bullet_text)
    return ImproveResumeResponse(**parsed)


@router.get("/{application_id}/results", response_model=MatchResponse)
def get_results(application_id: int, db: Session = Depends(get_db)) -> MatchResponse:
    record = analysis_service.get_latest_result(db, application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No analysis results found")

    breakdown_raw = json.loads(record.score_breakdown or "{}")
    return MatchResponse(
        id=record.id,
        application_id=record.application_id,
        resume_id=record.resume_id,
        match_score=record.match_score,
        matching_keywords=json.loads(record.matching_keywords or "[]"),
        missing_keywords=json.loads(record.missing_keywords or "[]"),
        score_breakdown=ScoreBreakdownSchema(
            skills=breakdown_raw.get("skills", 0),
            experience=breakdown_raw.get("experience", 0),
            keyword_coverage=breakdown_raw.get("keyword_coverage", 0),
            education=breakdown_raw.get("education", 0),
        ),
        created_at=record.created_at,
    )
