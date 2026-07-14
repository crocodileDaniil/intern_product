from app.db.models.checks import CheckIssueLevel, CheckProgram, CheckStatus, DetectedDocumentType
from app.services.checks import (
    IncomingDocument,
    ValidationIssue,
    calculate_final_status,
    detect_document_type,
    validate_package,
)


def test_detects_contract_by_cyrillic_name() -> None:
    assert detect_document_type("договор_47.pdf") == DetectedDocumentType.contract


def test_detects_invoice_with_yo_letter() -> None:
    assert detect_document_type("счёт_на_оплату.docx") == DetectedDocumentType.invoice


def test_federal_package_without_specification_is_rejected() -> None:
    result = validate_package(
        CheckProgram.federal,
        [
            IncomingDocument("договор.pdf", 1024),
            IncomingDocument("счет.pdf", 1024),
            IncomingDocument("акт.pdf", 1024),
        ],
    )

    assert result.status == CheckStatus.rejected
    assert any(
        issue.level == CheckIssueLevel.error and "спецификация" in issue.message
        for issue in result.issues
    )


def test_regional_package_without_specification_goes_to_neural_module() -> None:
    result = validate_package(
        CheckProgram.regional,
        [
            IncomingDocument("договор.pdf", 1024),
            IncomingDocument("счет.pdf", 1024),
            IncomingDocument("акт.pdf", 1024),
        ],
    )

    assert result.final_status == CheckStatus.approved
    assert result.status == CheckStatus.check_in_progress


def test_unknown_name_is_warning_not_rejection() -> None:
    result = validate_package(
        CheckProgram.regional,
        [
            IncomingDocument("договор.pdf", 1024),
            IncomingDocument("счет.pdf", 1024),
            IncomingDocument("акт.pdf", 1024),
            IncomingDocument("scan_0041.jpg", 1024),
        ],
    )

    assert result.final_status == CheckStatus.approved
    assert any(issue.level == CheckIssueLevel.warning for issue in result.issues)


def test_invalid_format_and_oversize_make_document_not_processable() -> None:
    result = validate_package(
        CheckProgram.regional,
        [
            IncomingDocument("договор.exe", 1024),
            IncomingDocument("счет.pdf", 21 * 1024 * 1024),
            IncomingDocument("акт.pdf", 1024),
        ],
    )

    documents_by_name = {document.name: document for document in result.documents}
    assert documents_by_name["договор.exe"].valid_for_processing is False
    assert documents_by_name["счет.pdf"].valid_for_processing is False
    assert all(issue.level == CheckIssueLevel.warning for issue in result.issues)


def test_final_status_is_rejected_when_any_error_exists() -> None:
    status = calculate_final_status(
        [
            ValidationIssue(CheckIssueLevel.warning, "warning"),
            ValidationIssue(CheckIssueLevel.error, "error"),
        ]
    )

    assert status == CheckStatus.rejected
