"""
Для хранения предупреждений и ошибок распознавания: 
- не найден ИНН
- низкая уверенность OCR
- проблемы с парсингом таблиц
- и т.д.
(можно будет вообще убрать) 
"""
import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Numeric,
    Date,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.init_base import Base

class ExtractionIssueSeverity(str, enum.Enum):
    info = "info"          # Информационное сообщение
    warning = "warning"    # Предупреждение, можно проверить вручную
    error = "error"        # Ошибка, без исправления данные нельзя подтвердить


class ExtractionIssueType(str, enum.Enum):
    missing_field = "missing_field"              # Не найдено обязательное поле
    invalid_format = "invalid_format"            # Поле найдено, но формат неверный
    calculation_mismatch = "calculation_mismatch"  # Не сходится арифметика
    low_confidence = "low_confidence"            # Низкая уверенность распознавания
    duplicate_suspected = "duplicate_suspected"  # Возможный дубль
    ocr_quality_low = "ocr_quality_low"          # Плохое качество OCR
    llm_json_invalid = "llm_json_invalid"        # LLM вернула невалидный JSON


class ExtractionIssue(Base):
    __tablename__ = "extraction_issues"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID проблемы извлечения",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
        comment="ID документа, в котором обнаружена проблема",
    )

    commercial_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=True,
        index=True,
        comment="ID КП, к которому относится проблема",
    )

    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offer_items.id"),
        nullable=True,
        comment="ID позиции КП, если проблема относится к конкретной позиции",
    )

    field_name = Column(
        String(255),
        nullable=True,
        comment="Название поля, с которым возникла проблема, например supplier.inn или items[0].price",
    )

    issue_type = Column(
        Enum(ExtractionIssueType),
        nullable=False,
        comment="Тип проблемы: отсутствующее поле, неверный формат, арифметическая ошибка и т.д.",
    )

    severity = Column(
        Enum(ExtractionIssueSeverity),
        nullable=False,
        default=ExtractionIssueSeverity.warning,
        comment="Серьёзность проблемы: info, warning или error",
    )

    message = Column(
        Text,
        nullable=False,
        comment="Человекочитаемое описание проблемы",
    )

    raw_value = Column(
        Text,
        nullable=True,
        comment="Сырое значение, которое вызвало проблему",
    )

    resolved = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Признак того, что пользователь или система исправили проблему",
    )

    resolved_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID пользователя, который исправил проблему",
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время исправления проблемы",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания проблемы",
    )

    document = relationship("Document", back_populates="extraction_issues")
    commercial_offer = relationship(
        "CommercialOffer",
        back_populates="extraction_issues",
    )