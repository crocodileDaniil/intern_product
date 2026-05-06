"""
Поставщики (вдруг стент много)
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

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID поставщика",
    )

    name = Column(
        Text,
        nullable=False,
        comment="Название поставщика: ООО, ИП или организация",
    )

    inn = Column(
        String(12),
        nullable=True,
        comment="ИНН поставщика. Для юрлиц обычно 10 цифр, для ИП 12 цифр",
    )

    kpp = Column(
        String(9),
        nullable=True,
        comment="КПП поставщика, если это юридическое лицо",
    )

    address = Column(
        Text,
        nullable=True,
        comment="Юридический или фактический адрес поставщика",
    )

    phone = Column(
        String(100),
        nullable=True,
        comment="Телефон поставщика",
    )

    email = Column(
        String(255),
        nullable=True,
        comment="Email поставщика",
    )

    website = Column(
        String(255),
        nullable=True,
        comment="Сайт поставщика, если он указан в КП",
    )

    raw_data = Column(
        JSONB,
        nullable=True,
        comment="Сырые данные о поставщике из LLM или документа",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания записи о поставщике",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата и время последнего обновления поставщика",
    )

    offers = relationship("CommercialOffer", back_populates="supplier")

    __table_args__ = (
        Index(
            "ix_suppliers_inn",
            "inn",
        ),
    )
