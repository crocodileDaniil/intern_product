from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.processing_jobs import ProcessingJob


class ProcessingJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, job_id: UUID) -> ProcessingJob | None:
        return self.db.get(ProcessingJob, job_id)

    def add(self, job: ProcessingJob) -> ProcessingJob:
        self.db.add(job)
        return job
