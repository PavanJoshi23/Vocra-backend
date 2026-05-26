from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate


def _fts_ids(db: Session, search: str) -> list[int]:
    """Return application IDs that match the FTS5 query, or [] if FTS unavailable."""
    try:
        rows = db.execute(
            text("SELECT rowid FROM applications_fts WHERE applications_fts MATCH :q"),
            {"q": search},
        ).fetchall()
        return [r[0] for r in rows]
    except Exception:
        return None  # signal caller to fall back to ILIKE


def list_applications(
    db: Session,
    *,
    search: str | None = None,
    status: ApplicationStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Application], int]:
    stmt = select(Application).where(Application.is_deleted.is_(False))

    if status is not None:
        stmt = stmt.where(Application.status == status)

    if search:
        fts_ids = _fts_ids(db, search.strip())
        if fts_ids is None:
            # FTS not available — fall back to ILIKE
            pattern = f"%{search.strip()}%"
            fts_filter = or_(
                Application.company_name.ilike(pattern),
                Application.job_title.ilike(pattern),
                Application.notes.ilike(pattern),
                Application.job_description.ilike(pattern),
            )
            stmt = stmt.where(fts_filter)
        elif fts_ids:
            stmt = stmt.where(Application.id.in_(fts_ids))
        else:
            return [], 0

    total_stmt = select(Application.id).where(Application.is_deleted.is_(False))
    if status is not None:
        total_stmt = total_stmt.where(Application.status == status)
    if search:
        fts_ids = _fts_ids(db, search.strip())
        if fts_ids is None:
            pattern = f"%{search.strip()}%"
            total_stmt = total_stmt.where(
                or_(
                    Application.company_name.ilike(pattern),
                    Application.job_title.ilike(pattern),
                    Application.notes.ilike(pattern),
                    Application.job_description.ilike(pattern),
                )
            )
        elif fts_ids:
            total_stmt = total_stmt.where(Application.id.in_(fts_ids))
        else:
            return [], 0

    total = len(db.scalars(total_stmt).all())
    items = list(
        db.scalars(
            stmt.order_by(Application.updated_at.desc()).offset(skip).limit(limit)
        ).all()
    )
    return items, total


def get_application(db: Session, application_id: int) -> Application | None:
    return db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.is_deleted.is_(False),
        )
    )


def create_application(db: Session, payload: ApplicationCreate) -> Application:
    application = Application(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update_application(
    db: Session, application: Application, payload: ApplicationUpdate
) -> Application:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application


def soft_delete_application(db: Session, application: Application) -> None:
    application.is_deleted = True
    db.commit()
