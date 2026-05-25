import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.parsers.resume_parser import extract_text
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.services import resumes as resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Can be overridden in tests
RESUME_STORAGE = Path(__file__).resolve().parents[2] / "storage" / "resumes"


def _sanitize_filename(filename: str) -> str:
    """Keep only safe characters, collapse runs of dashes/underscores."""
    name = re.sub(r"[^\w.\-]", "_", filename)
    name = re.sub(r"_+", "_", name)
    return name[:200]


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    name: str = Form(default=""),
    tags: str | None = Form(default=None),
    version: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> ResumeResponse:
    # Validate type
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_MIME_TYPES and suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF and DOCX files are accepted.",
        )

    # Read and size-check
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit.",
        )

    # Save to disk
    RESUME_STORAGE.mkdir(parents=True, exist_ok=True)
    safe_name = _sanitize_filename(file.filename or "resume")
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = RESUME_STORAGE / unique_name
    dest.write_bytes(contents)

    # Extract text
    parsed = extract_text(dest, file.content_type or "")

    display_name = name.strip() or Path(file.filename or "resume").stem

    resume = resume_service.create_resume(
        db,
        name=display_name,
        original_filename=file.filename or safe_name,
        file_path=dest,
        parsed_text=parsed,
        tags=tags,
        version=version,
    )
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=ResumeListResponse)
def list_resumes(db: Session = Depends(get_db)) -> ResumeListResponse:
    items, total = resume_service.list_resumes(db)
    return ResumeListResponse(items=items, total=total)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeResponse:
    resume = resume_service.get_resume(db, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: int, db: Session = Depends(get_db)) -> None:
    resume = resume_service.get_resume(db, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume_service.soft_delete_resume(db, resume)
