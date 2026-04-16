"""add session_engine fields to study_sessions and school_tasks

Revision ID: 20260416_0003
Revises: 20260416_0002
Create Date: 2026-04-16 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260416_0003"
down_revision = "20260416_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # study_sessions: add student_id, session_kind, runtime_state, steps, outcome
    op.add_column(
        "study_sessions",
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "study_sessions",
        sa.Column("session_kind", sa.String(30), nullable=False, server_default="homework"),
    )
    op.add_column(
        "study_sessions",
        sa.Column(
            "runtime_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "study_sessions",
        sa.Column(
            "steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "study_sessions",
        sa.Column(
            "outcome",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    # school_tasks: add pages, book_reference
    op.add_column(
        "school_tasks",
        sa.Column("pages", sa.String(100), nullable=True),
    )
    op.add_column(
        "school_tasks",
        sa.Column("book_reference", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("school_tasks", "book_reference")
    op.drop_column("school_tasks", "pages")
    op.drop_column("study_sessions", "outcome")
    op.drop_column("study_sessions", "steps")
    op.drop_column("study_sessions", "runtime_state")
    op.drop_column("study_sessions", "session_kind")
    op.drop_column("study_sessions", "student_id")
