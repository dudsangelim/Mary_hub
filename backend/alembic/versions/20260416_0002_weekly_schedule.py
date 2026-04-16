"""add weekly_schedule, fixed_activities and tutor_windows to student_profiles

Revision ID: 20260416_0002
Revises: 20260413_0001
Create Date: 2026-04-16 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260416_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column(
            "weekly_schedule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "fixed_activities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "tutor_windows",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "tutor_windows")
    op.drop_column("student_profiles", "fixed_activities")
    op.drop_column("student_profiles", "weekly_schedule")
