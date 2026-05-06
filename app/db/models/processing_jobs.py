"""SQLAlchemy model for document processing jobs."""
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.init_base import Base


class ProcessingJobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ProcessingJobType(str, enum.Enum):
    process_document = "process_document"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID задачи обработки",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
        comment="ID документа, к которому относится задача",
    )

    job_type = Column(
        Enum(ProcessingJobType),
        nullable=False,
        comment="Тип задачи: обработка документа, OCR, LLM-извлечение, embedding и т.д.",
    )

    status = Column(
        Enum(ProcessingJobStatus),
        nullable=False,
        default=ProcessingJobStatus.queued,
        index=True,
        comment="Текущий статус задачи",
    )

    attempt = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Номер текущей попытки выполнения задачи",
    )

    max_attempts = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Максимальное количество попыток выполнения задачи",
    )

    progress = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Прогресс выполнения конкретной задачи в процентах",
    )

    message = Column(
        Text,
        nullable=True,
        comment="Текущее сообщение по задаче, например 'Запущен OCR'",
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке, если задача упала",
    )

    payload = Column(
        JSONB,
        nullable=True,
        comment="Входные данные задачи, например настройки OCR или параметры обработки",
    )

    result = Column(
        JSONB,
        nullable=True,
        comment="Результат выполнения задачи в JSON-формате",
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время начала выполнения задачи",
    )

    finished_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время завершения задачи",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания задачи",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления задачи",
    )

    document = relationship("Document", back_populates="jobs")
