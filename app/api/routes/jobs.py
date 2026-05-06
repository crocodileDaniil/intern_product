from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.processing_job import ProcessingJobStatusResponse
from app.services.documents import DocumentService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}/status", response_model=ProcessingJobStatusResponse)
def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> ProcessingJobStatusResponse:
    service = DocumentService(db)
    return service.get_job_status(job_id)
