import csv
import io
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationUpdate,
)
from app.services import applications as application_service

router = APIRouter(prefix="/applications", tags=["applications"])


_EXPORT_FIELDS = [
    "id", "company_name", "job_title", "status", "application_date",
    "follow_up_date", "job_link", "salary_min", "salary_max",
    "notes", "job_description", "resume_id", "created_at", "updated_at",
]


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    search: str | None = Query(default=None),
    status: ApplicationStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    items, total = application_service.list_applications(
        db, search=search, status=status, skip=skip, limit=limit
    )
    return ApplicationListResponse(
        items=[ApplicationResponse.model_validate(item) for item in items],
        total=total,
    )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    application = application_service.create_application(db, payload)
    return ApplicationResponse.model_validate(application)


# /export must be declared BEFORE /{application_id} so FastAPI doesn't try to
# parse "export" as an integer path parameter.
@router.get("/export")
def export_applications(
    format: Literal["json", "csv"] = Query(..., description="Export format: json or csv"),
    db: Session = Depends(get_db),
) -> Response:
    items, _ = application_service.list_applications(db, limit=10_000)

    if format == "json":
        rows = []
        for item in items:
            row = {}
            for field in _EXPORT_FIELDS:
                val = getattr(item, field, None)
                row[field] = str(val) if val is not None else None
            rows.append(row)
        content = json.dumps(rows, indent=2, ensure_ascii=False)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=applications.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        row = {}
        for field in _EXPORT_FIELDS:
            val = getattr(item, field, None)
            row[field] = str(val) if val is not None else ""
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    application = application_service.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(application)


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    application = application_service.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    updated = application_service.update_application(db, application, payload)
    return ApplicationResponse.model_validate(updated)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> None:
    application = application_service.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    application_service.soft_delete_application(db, application)
