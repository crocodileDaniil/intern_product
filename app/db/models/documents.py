"""SQLAlchemy model for uploaded PDF documents."""
import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.init_base import Base


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    completed = "completed"
    needs_review = "needs_review"
    duplicate = "duplicate"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID загруженного документа",
    )

    original_filename = Column(
        String(255),
        nullable=False,
        comment="Оригинальное имя файла, которое загрузил пользователь",
    )

    content_type = Column(
        String(100),
        nullable=True,
        comment="MIME-тип файла, например application/pdf",
    )

    file_path = Column(
        Text,
        nullable=False,
        comment="Путь к сохранённому файлу в локальном хранилище, MinIO или S3",
    )

    file_sha256 = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA256-хэш файла для проверки точных дублей",
    )

    perceptual_hash = Column(
        String(64),
        nullable=True,
        comment="Перцептивный хэш первой страницы/изображения для поиска похожих сканов",
    )

    pages_count = Column(
        Integer,
        nullable=True,
        comment="Количество страниц в PDF",
    )

    file_size_bytes = Column(
        Integer,
        nullable=True,
        comment="Размер файла в байтах",
    )

    document_type = Column(
        String(50),
        nullable=True,
        comment="Тип документа: text_pdf, scanned_pdf, image_pdf, mixed_pdf, unknown",
    )

    has_text_layer = Column(
        Boolean,
        nullable=True,
        comment="Есть ли в PDF текстовый слой, который можно извлечь без OCR",
    )

    ocr_used = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Использовался ли OCR для распознавания текста",
    )

    processing_status = Column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.uploaded,
        comment="Текущий статус обработки документа",
    )

    progress = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Прогресс обработки в процентах от 0 до 100",
    )

    status_message = Column(
        Text,
        nullable=True,
        comment="Человекочитаемое сообщение о текущем этапе обработки",
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Текст ошибки, если обработка документа завершилась неудачно",
    )

    raw_text = Column(
        Text,
        nullable=True,
        comment="Сырой текст, извлечённый из PDF или полученный через OCR",
    )

    intermediate_json = Column(
        JSONB,
        nullable=True,
        comment="Промежуточная структура после парсинга PDF: страницы, текст, таблицы, OCR-данные",
    )

    llm_response = Column(
        JSONB,
        nullable=True,
        comment="Сырой ответ LLM/GigaChat до финальной нормализации и сохранения",
    )

    duplicate_of_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
        comment="ID оригинального документа, если текущий документ является дублем",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время загрузки документа",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления документа",
    )

    offers = relationship("CommercialOffer", back_populates="document")
    jobs = relationship("ProcessingJob", back_populates="document")
    extraction_issues = relationship("ExtractionIssue", back_populates="document")
    chunks = relationship("DocumentChunk", back_populates="document")
