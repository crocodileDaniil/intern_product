'''
ручные исправления пользователя
!!! НО ЕСЛИ ЭТОТ ФУНКЦИОНАЛ НЕ НУЖЕН, ТО УДАЛИТЬ ЭТОТ ФАЙЛ И ВСЕ ССЫЛКИ НА НЕГО
здесь будет находиться информация о том, 
какие поля пользователь исправил после автоматического распознавания
'''
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

class UserCorrection(Base):
    __tablename__ = "user_corrections"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID пользовательской правки",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
        comment="ID документа, в котором пользователь внёс исправление",
    )

    commercial_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=True,
        index=True,
        comment="ID КП, в котором пользователь внёс исправление",
    )

    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offer_items.id"),
        nullable=True,
        comment="ID позиции, если исправление относится к конкретной позиции",
    )

    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID пользователя, который внёс исправление",
    )

    field_name = Column(
        String(255),
        nullable=False,
        comment="Название исправленного поля, например supplier.inn или items[0].quantity",
    )

    old_value = Column(
        Text,
        nullable=True,
        comment="Старое значение, которое было извлечено автоматически",
    )

    new_value = Column(
        Text,
        nullable=True,
        comment="Новое значение, которое ввёл пользователь",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время внесения исправления",
    )