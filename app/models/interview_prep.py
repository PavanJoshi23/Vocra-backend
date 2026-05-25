from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class InterviewPrep(Base):
    __tablename__ = "interview_prep"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    technical_topics: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    behavioral_questions: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    coding_topics: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON
    study_roadmap: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
