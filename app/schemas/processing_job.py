from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.processing_jobs import ProcessingJobStatus


class ProcessingJobStatusResponse(BaseModel):
    job_id: UUID
    document_id: UUID
    status: ProcessingJobStatus
    progress: int
    message: str | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)
