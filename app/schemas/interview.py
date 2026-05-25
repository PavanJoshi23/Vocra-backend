from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InterviewGenerateRequest(BaseModel):
    application_id: int


class TechnicalTopic(BaseModel):
    topic: str
    priority: str
    why: str


class StudyWeek(BaseModel):
    week: int
    focus: str
    resources: list[str]


class InterviewPrepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    technical_topics: list[TechnicalTopic]
    behavioral_questions: list[str]
    coding_topics: list[str]
    study_roadmap: list[StudyWeek]
    from_cache: bool
    created_at: datetime
