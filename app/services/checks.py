from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.checks import (
    CheckIssueLevel,
    CheckProgram,
    CheckStatus,
    DetectedDocumentType,
    CheckDocument,
    DocumentCheck,
)
from app.schemas.check import (
    CheckDocumentResponse,
    CheckIssue,
    CheckListItem,
    CheckResponse,
)
from app.services.file_storage import delete_upload, save_upload
from app.services.hashing import sha256_bytes
from app.services.tasks import process_check_with_neural_stub


MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}

DOCUMENT_TYPE_LABELS = {
    DetectedDocumentType.contract: "договор",
    DetectedDocumentType.specification: "спецификация",
    DetectedDocumentType.invoice: "счет",
    DetectedDocumentType.act: "акт/УПД",
}

REQUIRED_DOCUMENTS = {
    CheckProgram.federal: {
        DetectedDocumentType.contract,
        DetectedDocumentType.specification,
        DetectedDocumentType.invoice,
        DetectedDocumentType.act,
    },
    CheckProgram.regional: {
        DetectedDocumentType.contract,
        DetectedDocumentType.invoice,
        DetectedDocumentType.act,
    },
}

TYPE_PATTERNS = {
    DetectedDocumentType.contract: (
        "договор",
        "контракт",
        "dogovor",
        "contract",
        "agreement",
    ),
    DetectedDocumentType.specification: (
        "спецификация",
        "specifikaciya",
        "specification",
        "spec",
    ),
    DetectedDocumentType.invoice: (
        "счет",
        "счёт",
        "schet",
        "invoice",
        "bill",
    ),
    DetectedDocumentType.act: (
        "акт",
        "упд",
        "upd",
        "act",
    ),
}


@dataclass(frozen=True)
class IncomingDocument:
    name: str
    size_bytes: int
    content_type: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    level: CheckIssueLevel
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level.value, "message": self.message}


@dataclass(frozen=True)
class ValidatedDocument:
    name: str
    detected_type: DetectedDocumentType
    size_kb: int
    valid_for_processing: bool


@dataclass(frozen=True)
class PackageValidationResult:
    status: CheckStatus
    final_status: CheckStatus
    status_label: str
    reason: str
    issues: list[ValidationIssue]
    documents: list[ValidatedDocument]


def detect_document_type(filename: str) -> DetectedDocumentType:
    normalized_name = _normalize_filename(filename)
    for document_type, patterns in TYPE_PATTERNS.items():
        if any(pattern in normalized_name for pattern in patterns):
            return document_type
    return DetectedDocumentType.unknown


def calculate_final_status(issues: list[ValidationIssue]) -> CheckStatus:
    if any(issue.level == CheckIssueLevel.error for issue in issues):
        return CheckStatus.rejected
    return CheckStatus.approved


def validate_package(
    program: CheckProgram,
    documents: list[IncomingDocument],
) -> PackageValidationResult:
    issues: list[ValidationIssue] = []
    validated_documents: list[ValidatedDocument] = []
    detected_types: set[DetectedDocumentType] = set()

    for document in documents:
        detected_type = detect_document_type(document.name)
        extension = Path(document.name).suffix.lower()
        size_kb = _size_kb(document.size_bytes)
        valid_extension = extension in ALLOWED_EXTENSIONS
        valid_size = document.size_bytes <= MAX_FILE_SIZE_BYTES

        if not valid_extension:
            issues.append(
                ValidationIssue(
                    level=CheckIssueLevel.warning,
                    message=(
                        f"Недопустимый формат файла: «{document.name}». "
                        "Допустимы PDF, DOCX, JPG, PNG."
                    ),
                )
            )

        if not valid_size:
            issues.append(
                ValidationIssue(
                    level=CheckIssueLevel.warning,
                    message=f"Размер файла превышает 20 МБ: «{document.name}»",
                )
            )

        if detected_type == DetectedDocumentType.unknown:
            issues.append(
                ValidationIssue(
                    level=CheckIssueLevel.warning,
                    message=f"Не удалось определить тип документа: «{document.name}»",
                )
            )
        else:
            detected_types.add(detected_type)

        validated_documents.append(
            ValidatedDocument(
                name=document.name,
                detected_type=detected_type,
                size_kb=size_kb,
                valid_for_processing=valid_extension and valid_size,
            )
        )

    for missing_type in sorted(
        REQUIRED_DOCUMENTS[program] - detected_types,
        key=lambda document_type: document_type.value,
    ):
        issues.append(
            ValidationIssue(
                level=CheckIssueLevel.error,
                message=(
                    "Отсутствует обязательный документ: "
                    f"{DOCUMENT_TYPE_LABELS[missing_type]}"
                ),
            )
        )

    final_status = calculate_final_status(issues)
    status_for_response = (
        CheckStatus.rejected
        if final_status == CheckStatus.rejected
        else CheckStatus.check_in_progress
    )
    return PackageValidationResult(
        status=status_for_response,
        final_status=final_status,
        status_label=_status_label(status_for_response),
        reason=_status_reason(status_for_response, issues),
        issues=issues,
        documents=validated_documents,
    )


class CheckService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def create_check(
        self,
        program: CheckProgram,
        files: list[UploadFile],
        background_tasks: BackgroundTasks,
    ) -> CheckResponse:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нужно загрузить хотя бы один файл",
            )

        uploaded_files = []
        for index, file in enumerate(files, start=1):
            content = await file.read()
            filename = file.filename or f"document_{index}"
            uploaded_files.append(
                {
                    "filename": filename,
                    "content_type": file.content_type,
                    "content": content,
                }
            )

        validation = validate_package(
            program=program,
            documents=[
                IncomingDocument(
                    name=uploaded_file["filename"],
                    size_bytes=len(uploaded_file["content"]),
                    content_type=uploaded_file["content_type"],
                )
                for uploaded_file in uploaded_files
            ],
        )

        task_id = uuid4() if validation.status == CheckStatus.check_in_progress else None
        extracted = (
            {
                "message": (
                    "Файлы прошли базовую проверку и переданы в нейромодуль. "
                    "Извлечение реквизитов заменено заглушкой."
                ),
                "task_id": str(task_id),
            }
            if task_id is not None
            else {}
        )

        stored_paths: list[str] = []
        try:
            check = DocumentCheck(
                program=program,
                status=validation.status,
                status_label=validation.status_label,
                reason=validation.reason,
                issues=[issue.to_dict() for issue in validation.issues],
                extracted=extracted,
                task_id=task_id,
                neural_status_message=(
                    "Файлы обрабатываются нейромодулем"
                    if task_id is not None
                    else None
                ),
                documents_count=len(uploaded_files),
            )
            self.db.add(check)
            self.db.flush()

            version_offsets: dict[tuple[str, DetectedDocumentType], int] = {}
            for uploaded_file, validated_document in zip(uploaded_files, validation.documents):
                filename = uploaded_file["filename"]
                content = uploaded_file["content"]
                file_path = save_upload(content, filename)
                stored_paths.append(file_path)
                version_key = (filename, validated_document.detected_type)
                version_offsets[version_key] = version_offsets.get(version_key, 0) + 1

                check_document = CheckDocument(
                    check_id=check.id,
                    original_filename=filename,
                    detected_type=validated_document.detected_type,
                    content_type=uploaded_file["content_type"],
                    file_path=file_path,
                    file_sha256=sha256_bytes(content),
                    file_size_bytes=len(content),
                    size_kb=validated_document.size_kb,
                    version=self._next_document_version(
                        filename=filename,
                        detected_type=validated_document.detected_type,
                    )
                    + version_offsets[version_key]
                    - 1,
                    valid_for_processing=validated_document.valid_for_processing,
                    processing_message=(
                        "Файл обрабатывается нейромодулем"
                        if validated_document.valid_for_processing and task_id is not None
                        else "Файл не передан в нейромодуль после базовой проверки"
                    ),
                )
                self.db.add(check_document)

            self.db.commit()
            self.db.refresh(check)
        except OSError as exc:
            self.db.rollback()
            _delete_saved_files(stored_paths)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось сохранить файл: {exc}",
            ) from exc
        except Exception as exc:
            self.db.rollback()
            _delete_saved_files(stored_paths)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось создать проверку: {exc}",
            ) from exc

        if task_id is not None:
            background_tasks.add_task(process_check_with_neural_stub, check.id, task_id)

        return self._to_response(check)

    def list_checks(self) -> list[CheckListItem]:
        checks = (
            self.db.query(DocumentCheck)
            .order_by(DocumentCheck.checked_at.desc(), DocumentCheck.created_at.desc())
            .all()
        )
        return [
            CheckListItem(
                id=check.id,
                date=check.checked_at,
                program=check.program,
                status=check.status,
                documents_count=check.documents_count,
            )
            for check in checks
        ]

    def get_check(self, check_id: UUID) -> CheckResponse:
        check = self.db.get(DocumentCheck, check_id)
        if check is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проверка не найдена")
        return self._to_response(check)

    def _next_document_version(
        self,
        filename: str,
        detected_type: DetectedDocumentType,
    ) -> int:
        max_version = (
            self.db.query(func.max(CheckDocument.version))
            .filter(
                CheckDocument.original_filename == filename,
                CheckDocument.detected_type == detected_type,
            )
            .scalar()
        )
        return int(max_version or 0) + 1

    @staticmethod
    def _to_response(check: DocumentCheck) -> CheckResponse:
        return CheckResponse(
            check_id=check.id,
            task_id=check.task_id,
            status=check.status,
            status_label=check.status_label,
            reason=check.reason,
            issues=[CheckIssue(**issue) for issue in check.issues],
            documents=[
                CheckDocumentResponse(
                    name=document.original_filename,
                    detected_type=document.detected_type,
                    size_kb=document.size_kb,
                    version=document.version,
                    valid_for_processing=document.valid_for_processing,
                    processing_message=document.processing_message,
                )
                for document in check.documents
            ],
            extracted=check.extracted,
            checked_at=check.checked_at,
        )


def _normalize_filename(filename: str) -> str:
    return Path(filename).stem.lower().replace("ё", "е")


def _size_kb(size_bytes: int) -> int:
    return max(1, (size_bytes + 1023) // 1024)


def _status_label(status_value: CheckStatus) -> str:
    labels = {
        CheckStatus.approved: "Можно заявлять в банк",
        CheckStatus.rejected: "Нельзя заявлять в банк",
        CheckStatus.check_in_progress: "Пакет обрабатывается нейромодулем",
    }
    return labels[status_value]


def _status_reason(
    status_value: CheckStatus,
    issues: list[ValidationIssue],
) -> str:
    if status_value == CheckStatus.rejected:
        first_error = next(
            issue for issue in issues if issue.level == CheckIssueLevel.error
        )
        return first_error.message
    if status_value == CheckStatus.check_in_progress:
        return "Базовая проверка пройдена. Файлы обрабатываются нейромодулем."
    return "Нарушений не найдено."


def _delete_saved_files(paths: list[str]) -> None:
    for path in paths:
        delete_upload(path)
