import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.ollama_client import OllamaTimeoutError, OllamaUnavailableError
from app.database import get_db
from app.schemas.interview import InterviewGenerateRequest, InterviewPrepResponse
from app.services.interview_prep import generate_prep

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/generate", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    body: InterviewGenerateRequest,
    db: Session = Depends(get_db),
) -> InterviewPrepResponse:
    try:
        record = await generate_prep(db, body.application_id)
        db.commit()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (OllamaUnavailableError, OllamaTimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {exc}",
        )

    return InterviewPrepResponse(
        id=record.id,
        application_id=record.application_id,
        technical_topics=json.loads(record.technical_topics or "[]"),
        behavioral_questions=json.loads(record.behavioral_questions or "[]"),
        coding_topics=json.loads(record.coding_topics or "[]"),
        study_roadmap=json.loads(record.study_roadmap or "[]"),
        from_cache=record.from_cache,
        created_at=record.created_at,
    )
