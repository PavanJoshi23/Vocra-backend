import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import (
    ExtractSkillsRequest,
    ExtractSkillsResponse,
    ExtractedSkillItem,
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
