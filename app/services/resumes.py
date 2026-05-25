from pathlib import Path

from sqlalchemy.orm import Session

from app.models.resume import Resume


def list_resumes(db: Session) -> tuple[list[Resume], int]:
    q = db.query(Resume).filter(Resume.is_deleted == False).order_by(Resume.created_at.desc())  # noqa: E712
    items = q.all()
    return items, len(items)


def get_resume(db: Session, resume_id: int) -> Resume | None:
    return (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.is_deleted == False)  # noqa: E712
        .first()
    )


def create_resume(
    db: Session,
    name: str,
    original_filename: str,
    file_path: Path,
    parsed_text: str,
    tags: str | None = None,
    version: str | None = None,
) -> Resume:
    resume = Resume(
        name=name,
        original_filename=original_filename,
        file_path=str(file_path),
        parsed_text=parsed_text,
        tags=tags,
        version=version,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def soft_delete_resume(db: Session, resume: Resume) -> None:
    resume.is_deleted = True
    db.commit()
