from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    original_filename: str
    file_path: str
    tags: str | None
    version: str | None
    parsed_text: str | None
    created_at: datetime


class ResumeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    original_filename: str
    tags: str | None
    version: str | None
    created_at: datetime


class ResumeListResponse(BaseModel):
    items: list[ResumeListItem]
    total: int
