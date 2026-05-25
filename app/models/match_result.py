from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, nullable=False)
    resume_id: Mapped[int] = mapped_column(Integer, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    matching_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    missing_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON
    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
