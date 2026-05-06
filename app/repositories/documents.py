from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.documents import Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def get_by_sha256(self, file_sha256: str) -> Document | None:
        return self.db.query(Document).filter(Document.file_sha256 == file_sha256).first()

    def add(self, document: Document) -> Document:
        self.db.add(document)
        return document
