from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.documents import Document, DocumentStatus
from app.db.models.processing_jobs import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
)
from app.repositories.documents import DocumentRepository
from app.repositories.processing_jobs import ProcessingJobRepository
from app.schemas.document import DocumentStatusResponse, DocumentUploadResponse
from app.schemas.processing_job import ProcessingJobStatusResponse
from app.services.file_storage import delete_upload, save_upload
from app.services.hashing import sha256_bytes


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.jobs = ProcessingJobRepository(db)

    async def upload_pdf(self, file: UploadFile) -> DocumentUploadResponse:
        if not self._looks_like_pdf(file):
            raise HTTPException(status_code=400, detail="Можно загружать только PDF-файлы")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Файл пустой")

        file_path: str | None = None
        file_sha256 = sha256_bytes(content)

        existing_document = self.documents.get_by_sha256(file_sha256)
        if existing_document is not None:
            return DocumentUploadResponse(
                document_id=existing_document.id,
                job_id=None,
                status=DocumentStatus.duplicate,
                message="Такой файл уже был загружен",
            )

        try:
            file_path = save_upload(content, file.filename or "document.pdf")

            document = Document(
                original_filename=file.filename or "document.pdf",
                content_type=file.content_type,
                file_path=file_path,
                file_sha256=file_sha256,
                file_size_bytes=len(content),
                processing_status=DocumentStatus.queued,
                progress=0,
                status_message="Файл загружен, задача создана",
            )
            self.documents.add(document)
            self.db.flush()

            job = ProcessingJob(
                document_id=document.id,
                job_type=ProcessingJobType.process_document,
                status=ProcessingJobStatus.queued,
                attempt=0,
                max_attempts=3,
                progress=0,
                message="Задача ожидает обработки",
                payload={"document_id": str(document.id)},
            )
            self.jobs.add(job)
            self.db.commit()
            self.db.refresh(document)
            self.db.refresh(job)
        except IntegrityError:
            self.db.rollback()
            if file_path is not None:
                delete_upload(file_path)
            existing_document = self.documents.get_by_sha256(file_sha256)
            if existing_document is None:
                raise HTTPException(
                    status_code=500,
                    detail="Не удалось создать документ из-за конфликта данных",
                ) from None
            return DocumentUploadResponse(
                document_id=existing_document.id,
                job_id=None,
                status=DocumentStatus.duplicate,
                message="Такой файл уже был загружен",
            )
        except OSError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось сохранить файл: {exc}",
            ) from exc
        except Exception as exc:
            self.db.rollback()
            if file_path is not None:
                delete_upload(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Не удалось создать документ и задачу: {exc}",
            ) from exc

        return DocumentUploadResponse(
            document_id=document.id,
            job_id=job.id,
            status=document.processing_status,
            message=document.status_message or "Файл загружен, задача создана",
        )

    def get_document_status(self, document_id: UUID) -> DocumentStatusResponse:
        document = self.documents.get_by_id(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Документ не найден")

        return DocumentStatusResponse(
            document_id=document.id,
            status=document.processing_status,
            progress=document.progress,
            message=document.status_message,
            error_message=document.error_message,
        )

    def get_job_status(self, job_id: UUID) -> ProcessingJobStatusResponse:
        job = self.jobs.get_by_id(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        return ProcessingJobStatusResponse(
            job_id=job.id,
            document_id=job.document_id,
            status=job.status,
            progress=job.progress,
            message=job.message,
            error_message=job.error_message,
        )

    @staticmethod
    def _looks_like_pdf(file: UploadFile) -> bool:
        filename = (file.filename or "").lower()
        content_type = (file.content_type or "").lower()
        return content_type == "application/pdf" or filename.endswith(".pdf")
