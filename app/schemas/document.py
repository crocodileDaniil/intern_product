from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.documents import DocumentStatus


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    job_id: UUID | None
    status: DocumentStatus
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    progress: int
    message: str | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)
