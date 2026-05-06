"""
Коммерческие предложения (КП). Общая информация о конкретном предложении
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

class OfferStatus(str, enum.Enum):
    draft = "draft"                          # Черновик после автоматического извлечения
    ready_for_review = "ready_for_review"    # Готово к проверке пользователем
    needs_review = "needs_review"            # Требуется ручная проверка
    approved = "approved"                    # Пользователь подтвердил КП
    rejected = "rejected"                    # Пользователь отклонил КП
    duplicate = "duplicate"                  # КП признано дублем


class CommercialOffer(Base):
    __tablename__ = "commercial_offers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID коммерческого предложения",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
        comment="ID документа, из которого извлечено КП",
    )

    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
        comment="ID поставщика, который прислал КП",
    )

    quote_number = Column(
        String(100),
        nullable=True,
        comment="Номер коммерческого предложения, если указан",
    )

    quote_date = Column(
        Date,
        nullable=True,
        comment="Дата коммерческого предложения",
    )

    valid_until = Column(
        Date,
        nullable=True,
        comment="Дата, до которой действительно КП",
    )

    category = Column(
        String(255),
        nullable=True,
        comment="Категория закупки, например 'чайники', 'микроволновые печи'",
    )

    currency = Column(
        String(10),
        nullable=False,
        default="RUB",
        comment="Валюта КП, например RUB, USD, EUR",
    )

    total_amount_without_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Итоговая сумма КП без НДС",
    )

    total_amount_with_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Итоговая сумма КП с НДС",
    )

    vat_included = Column(
        Boolean,
        nullable=True,
        comment="Признак того, что цены включают НДС",
    )

    vat_rate = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Ставка НДС, например 20.00",
    )

    payment_terms = Column(
        Text,
        nullable=True,
        comment="Условия оплаты: предоплата, отсрочка, оплата по факту и т.д.",
    )

    delivery_terms = Column(
        Text,
        nullable=True,
        comment="Условия доставки или поставки",
    )

    warranty_terms = Column(
        Text,
        nullable=True,
        comment="Гарантийные условия, если указаны в КП",
    )

    additional_info = Column(
        Text,
        nullable=True,
        comment="Дополнительная информация из КП, не попавшая в другие поля",
    )

    status = Column(
        Enum(OfferStatus),
        nullable=False,
        default=OfferStatus.draft,
        index=True,
        comment="Статус КП: черновик, требует проверки, подтверждено и т.д.",
    )

    extraction_confidence = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Оценка уверенности извлечения данных, например 0.85",
    )

    normalized_json = Column(
        JSONB,
        nullable=True,
        comment="Нормализованный JSON коммерческого предложения после обработки",
    )

    raw_llm_json = Column(
        JSONB,
        nullable=True,
        comment="Сырой JSON, который вернула LLM/GigaChat",
    )

    approved_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID пользователя, который подтвердил КП",
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время подтверждения КП пользователем",
    )

    duplicate_of_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=True,
        comment="ID оригинального КП, если текущее КП является дублем",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания КП",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления КП",
    )

    document = relationship("Document", back_populates="offers")
    supplier = relationship("Supplier", back_populates="offers")
    items = relationship("CommercialOfferItem", back_populates="commercial_offer")
    extraction_issues = relationship(
        "ExtractionIssue",
        back_populates="commercial_offer",
    )

    __table_args__ = (
        Index(
            "ix_commercial_offers_supplier_quote_date",
            "supplier_id",
            "quote_number",
            "quote_date",
        ),
    )