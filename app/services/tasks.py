"""Фоновые задачи, которые пока заменяют реальный нейромодуль.

Настоящее извлечение реквизитов выходит за рамки тестового задания. Здесь
мы явно показываем точку интеграции: API создает task_id, а фоновая задача
помечает пакет как обработанный заглушкой.
"""
from uuid import UUID

from app.db.models.checks import CheckStatus, DocumentCheck
from app.db.session import SessionLocal


def process_check_with_neural_stub(check_id: UUID, task_id: UUID) -> None:
    db = SessionLocal()
    try:
        check = db.get(DocumentCheck, check_id)
        if check is None or check.status != CheckStatus.check_in_progress:
            return

        check.status = CheckStatus.approved
        check.status_label = "Можно заявлять в банк"
        check.reason = (
            "Базовая проверка пройдена. Нейромодуль заменен заглушкой "
            "и не выявил дополнительных нарушений."
        )
        check.neural_status_message = "Файлы обработаны нейромодулем-заглушкой"
        check.extracted = {
            "message": "Извлечение реквизитов выполнено заглушкой нейромодуля.",
            "task_id": str(task_id),
            "contractor": None,
            "amount": None,
            "date": None,
            "subject": None,
        }
        for document in check.documents:
            if document.valid_for_processing:
                document.processing_message = "Файл обработан нейромодулем-заглушкой"

        db.commit()
    finally:
        db.close()
