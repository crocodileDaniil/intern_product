"""SQLAlchemy models for credit document package checks."""
import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.init_base import Base


class CheckProgram(str, enum.Enum):
    federal = "federal"
    regional = "regional"


class CheckStatus(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    check_in_progress = "check_in_progress"


class CheckIssueLevel(str, enum.Enum):
    error = "error"
    warning = "warning"


class DetectedDocumentType(str, enum.Enum):
    contract = "contract"
    specification = "specification"
    invoice = "invoice"
    act = "act"
    unknown = "unknown"


class DocumentCheck(Base):
    __tablename__ = "checks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID проверки пакета документов",
    )
    program = Column(
        Enum(CheckProgram),
        nullable=False,
        index=True,
        comment="Программа льготного кредитования: federal или regional",
    )
    status = Column(
        Enum(CheckStatus),
        nullable=False,
        default=CheckStatus.check_in_progress,
        index=True,
        comment="Итоговый статус проверки пакета",
    )
    status_label = Column(
        String(255),
        nullable=False,
        comment="Человекочитаемая подпись статуса",
    )
    reason = Column(
        Text,
        nullable=False,
        comment="Краткая причина текущего статуса",
    )
    issues = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Список найденных ошибок и предупреждений",
    )
    extracted = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Данные, извлечённые нейромодулем. На тестовом этапе заглушка.",
    )
    task_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID фоновой задачи нейромодуля",
    )
    neural_status_message = Column(
        Text,
        nullable=True,
        comment="Статус передачи файлов в нейромодуль",
    )
    documents_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество документов в загруженном пакете",
    )
    checked_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время запуска проверки",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания записи",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления записи",
    )

    documents = relationship(
        "CheckDocument",
        back_populates="check",
        cascade="all, delete-orphan",
        order_by="CheckDocument.created_at",
    )


class CheckDocument(Base):
    __tablename__ = "check_documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID документа внутри проверки",
    )
    check_id = Column(
        UUID(as_uuid=True),
        ForeignKey("checks.id"),
        nullable=False,
        index=True,
        comment="ID проверки, к которой относится документ",
    )
    original_filename = Column(
        String(255),
        nullable=False,
        comment="Оригинальное имя файла",
    )
    detected_type = Column(
        Enum(DetectedDocumentType),
        nullable=False,
        default=DetectedDocumentType.unknown,
        index=True,
        comment="Тип документа, определённый по имени файла",
    )
    content_type = Column(
        String(100),
        nullable=True,
        comment="MIME-тип файла",
    )
    file_path = Column(
        Text,
        nullable=False,
        comment="Путь к сохранённому файлу",
    )
    file_sha256 = Column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA256-хэш содержимого файла",
    )
    file_size_bytes = Column(
        Integer,
        nullable=False,
        comment="Размер файла в байтах",
    )
    size_kb = Column(
        Integer,
        nullable=False,
        comment="Размер файла в килобайтах для API-ответа",
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Версия документа при повторной загрузке",
    )
    valid_for_processing = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Можно ли передавать файл в нейромодуль по формату и размеру",
    )
    processing_message = Column(
        Text,
        nullable=False,
        default="Файл ожидает обработки нейромодулем",
        comment="Статус обработки файла нейромодулем",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время загрузки документа",
    )

    check = relationship("DocumentCheck", back_populates="documents")
