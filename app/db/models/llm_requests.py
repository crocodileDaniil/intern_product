'''
история обращений к GigaChat
чтобы можно было отслеживать и потом отлаживать, 
если что-то пошло не так
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
class LLMRequestStatus(str, enum.Enum):
    success = "success"    # Запрос успешно выполнен
    failed = "failed"      # Запрос завершился ошибкой


class LLMRequest(Base):
    __tablename__ = "llm_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный ID обращения к LLM",
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
        index=True,
        comment="ID документа, если запрос к LLM связан с обработкой документа",
    )

    commercial_offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_offers.id"),
        nullable=True,
        index=True,
        comment="ID КП, если запрос к LLM связан с конкретным коммерческим предложением",
    )

    provider = Column(
        String(100),
        nullable=False,
        default="gigachat",
        comment="Провайдер LLM, например gigachat",
    )

    model = Column(
        String(100),
        nullable=True,
        comment="Название модели, которая использовалась",
    )

    request_type = Column(
        String(100),
        nullable=False,
        comment="Тип запроса: extract_commercial_offer, classify_user_query, generate_answer, create_embedding",
    )

    prompt = Column(
        Text,
        nullable=True,
        comment="Текст промпта, отправленного в LLM",
    )

    request_payload = Column(
        JSONB,
        nullable=True,
        comment="Полное тело запроса к LLM в JSON-формате",
    )

    response_payload = Column(
        JSONB,
        nullable=True,
        comment="Полный ответ LLM в JSON-формате",
    )

    status = Column(
        Enum(LLMRequestStatus),
        nullable=False,
        comment="Статус запроса к LLM: success или failed",
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Текст ошибки, если запрос к LLM завершился неудачно",
    )

    input_tokens = Column(
        Integer,
        nullable=True,
        comment="Количество входных токенов, если провайдер возвращает эту информацию",
    )

    output_tokens = Column(
        Integer,
        nullable=True,
        comment="Количество выходных токенов, если провайдер возвращает эту информацию",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время обращения к LLM",
    )