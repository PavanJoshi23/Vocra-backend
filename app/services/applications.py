from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate


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
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Application.company_name.ilike(pattern),
                Application.job_title.ilike(pattern),
                Application.notes.ilike(pattern),
                Application.job_description.ilike(pattern),
            )
        )

    count_stmt = select(Application.id).where(Application.is_deleted.is_(False))
    if status is not None:
        count_stmt = count_stmt.where(Application.status == status)
    if search:
        pattern = f"%{search.strip()}%"
        count_stmt = count_stmt.where(
            or_(
                Application.company_name.ilike(pattern),
                Application.job_title.ilike(pattern),
                Application.notes.ilike(pattern),
                Application.job_description.ilike(pattern),
            )
        )

    total = len(db.scalars(count_stmt).all())
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
