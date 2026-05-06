"""Legacy schema module kept for compatibility."""

from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.document import DocumentStatusResponse, DocumentUploadResponse
from app.schemas.processing_job import ProcessingJobStatusResponse

__all__ = [
    "AgentQueryRequest",
    "AgentQueryResponse",
    "DocumentStatusResponse",
    "DocumentUploadResponse",
    "ProcessingJobStatusResponse",
]
