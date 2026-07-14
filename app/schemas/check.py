from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.checks import (
    CheckIssueLevel,
    CheckProgram,
    CheckStatus,
    DetectedDocumentType,
)


class CheckIssue(BaseModel):
    level: CheckIssueLevel
    message: str


class CheckDocumentResponse(BaseModel):
    name: str
    detected_type: DetectedDocumentType
    size_kb: int


class CheckResponse(BaseModel):
    check_id: UUID
    task_id: UUID | None
    status: CheckStatus
    status_label: str
    reason: str
    issues: list[CheckIssue]
    documents: list[CheckDocumentResponse]
    extracted: dict
    checked_at: datetime


class CheckListItem(BaseModel):
    id: UUID
    date: datetime
    program: CheckProgram
    status: CheckStatus
    documents_count: int

    model_config = ConfigDict(from_attributes=True)
