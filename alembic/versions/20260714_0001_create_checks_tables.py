"""create checks tables

Revision ID: 20260714_0001
Revises:
Create Date: 2026-07-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260714_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "program",
            sa.Enum("federal", "regional", name="checkprogram"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "approved",
                "rejected",
                "check_in_progress",
                name="checkstatus",
            ),
            nullable=False,
        ),
        sa.Column("status_label", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("issues", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extracted", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("neural_status_message", sa.Text(), nullable=True),
        sa.Column("documents_count", sa.Integer(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checks_program"), "checks", ["program"], unique=False)
    op.create_index(op.f("ix_checks_status"), "checks", ["status"], unique=False)
    op.create_index(op.f("ix_checks_task_id"), "checks", ["task_id"], unique=False)

    op.create_table(
        "check_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column(
            "detected_type",
            sa.Enum(
                "contract",
                "specification",
                "invoice",
                "act",
                "unknown",
                name="detecteddocumenttype",
            ),
            nullable=False,
        ),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("size_kb", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("valid_for_processing", sa.Boolean(), nullable=False),
        sa.Column("processing_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["check_id"], ["checks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_check_documents_check_id"), "check_documents", ["check_id"], unique=False)
    op.create_index(op.f("ix_check_documents_detected_type"), "check_documents", ["detected_type"], unique=False)
    op.create_index(op.f("ix_check_documents_file_sha256"), "check_documents", ["file_sha256"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_check_documents_file_sha256"), table_name="check_documents")
    op.drop_index(op.f("ix_check_documents_detected_type"), table_name="check_documents")
    op.drop_index(op.f("ix_check_documents_check_id"), table_name="check_documents")
    op.drop_table("check_documents")
    op.drop_index(op.f("ix_checks_task_id"), table_name="checks")
    op.drop_index(op.f("ix_checks_status"), table_name="checks")
    op.drop_index(op.f("ix_checks_program"), table_name="checks")
    op.drop_table("checks")
    op.execute("DROP TYPE IF EXISTS detecteddocumenttype")
    op.execute("DROP TYPE IF EXISTS checkstatus")
    op.execute("DROP TYPE IF EXISTS checkprogram")
