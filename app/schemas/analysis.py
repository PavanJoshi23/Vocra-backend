from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExtractSkillsRequest(BaseModel):
    text: str


class ExtractedSkillItem(BaseModel):
    skill_name: str
    skill_type: str | None
    importance_score: float


class ExtractSkillsResponse(BaseModel):
    skills: list[ExtractedSkillItem]


class MatchRequest(BaseModel):
    application_id: int
    resume_id: int


class ScoreBreakdownSchema(BaseModel):
    skills: int
    experience: int
    keyword_coverage: int
    education: int


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    resume_id: int
    match_score: float
    matching_keywords: list[str]
    missing_keywords: list[str]
    score_breakdown: ScoreBreakdownSchema
    created_at: datetime


class ImproveResumeRequest(BaseModel):
    resume_id: int
    application_id: int
    bullet_text: str


class ImproveResumeResponse(BaseModel):
    original: str
    suggestion: str
    changes: list[str]
