from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InterviewGenerateRequest(BaseModel):
    application_id: int


class InterviewPrepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    topics: list[str]
    from_cache: bool
    created_at: datetime
