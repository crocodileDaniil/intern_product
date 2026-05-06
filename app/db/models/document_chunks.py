'''
для RAG/поиска по смыслу. 
Например, чтобы находить условия оплаты, гарантии, доставку, ограничения.
Если вообще будем векторизовать 
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

class ChunkType(str, enum.Enum):
    raw_text = "raw_text"                  # Обычный фрагмент сырого текста
    payment_terms = "payment_terms"        # Условия оплаты
    delivery_terms = "delivery_terms"      # Условия доставки
    warranty_terms = "warranty_terms"      # Гарантийные условия
    additional_info = "additional_info"    # Дополнительная информация
    item_description = "item_description"  # Описание конкретной позиции


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID текстового фрагмента",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
        comment="ID документа, из которого взят фрагмент",
    )

    commercial_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=True,
        index=True,
        comment="ID КП, к которому относится фрагмент",
    )

    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offer_items.id"),
        nullable=True,
        index=True,
        comment="ID позиции, если фрагмент относится к конкретному товару",
    )

    chunk_type = Column(
        Enum(ChunkType),
        nullable=False,
        comment="Тип фрагмента: условия оплаты, доставка, описание позиции, сырой текст",
    )

    content = Column(
        Text,
        nullable=False,
        comment="Текст фрагмента, который будет использоваться для поиска или векторизации",
    )

    page_number = Column(
        Integer,
        nullable=True,
        comment="Номер страницы PDF, откуда взят фрагмент",
    )

    chunk_index = Column(
        Integer,
        nullable=True,
        comment="Порядковый номер фрагмента внутри документа",
    )

    chunk_metadata = Column(
        JSONB,
        nullable=True,
        comment="Дополнительные метаданные фрагмента: координаты, источник, уверенность и т.д.",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время создания фрагмента",
    )

    document = relationship("Document", back_populates="chunks")