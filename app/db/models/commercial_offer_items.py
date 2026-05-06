"""
Для хранение дукументов, загружаемых пользователем (КП). 
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

class CommercialOfferItem(Base):
    __tablename__ = "commercial_offer_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID позиции КП",
    )

    commercial_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=False,
        index=True,
        comment="ID коммерческого предложения, к которому относится позиция",
    )

    position_number = Column(
        Integer,
        nullable=True,
        comment="Номер позиции в КП, если он указан",
    )

    name = Column(
        Text,
        nullable=False,
        comment="Наименование товара или услуги",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Описание, характеристики или дополнительные сведения о позиции",
    )

    sku = Column(
        String(255),
        nullable=True,
        comment="SKU или внутренний код товара, если указан",
    )

    article = Column(
        String(255),
        nullable=True,
        comment="Артикул товара, если указан в КП",
    )

    quantity = Column(
        Numeric(14, 3),
        nullable=True,
        comment="Количество товара или услуги",
    )

    unit = Column(
        String(50),
        nullable=True,
        comment="Единица измерения: шт, кг, м, услуга и т.д.",
    )

    unit_price_without_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Цена за единицу без НДС",
    )

    unit_price_with_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Цена за единицу с НДС",
    )

    total_price_without_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Сумма по позиции без НДС",
    )

    total_price_with_vat = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Сумма по позиции с НДС",
    )

    vat_rate = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Ставка НДС по позиции",
    )

    availability = Column(
        Text,
        nullable=True,
        comment="Наличие товара: в наличии, под заказ, склад и т.д.",
    )

    delivery_time = Column(
        Text,
        nullable=True,
        comment="Срок поставки конкретной позиции, если отличается от общего срока",
    )

    raw_text = Column(
        Text,
        nullable=True,
        comment="Сырой фрагмент текста, из которого была извлечена позиция",
    )

    raw_data = Column(
        JSONB,
        nullable=True,
        comment="Сырые данные позиции из LLM или таблицы PDF",
    )

    extraction_confidence = Column(
        Numeric(5, 2),
        nullable=True,
        comment="Оценка уверенности распознавания этой позиции",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания позиции",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления позиции",
    )

    commercial_offer = relationship("CommercialOffer", back_populates="items")

    __table_args__ = (
        Index("ix_offer_items_name", "name"),
    )