"""initial schema

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def uuid_column(nullable: bool = False) -> sa.Column[sa.UUID]:
    return sa.Column(
        postgresql.UUID(as_uuid=True),
        primary_key=not nullable,
        nullable=nullable,
    )


def upgrade() -> None:
    op.create_table(
        "families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="America/Sao_Paulo"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "guardians",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="parent"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("grade", sa.String(length=50), nullable=False),
        sa.Column("grade_label", sa.String(length=100), nullable=False),
        sa.Column("school_name", sa.String(length=255), nullable=True),
        sa.Column("school_shift", sa.String(length=20), nullable=True),
        sa.Column("avatar_color", sa.String(length=7), nullable=False, server_default="#6366f1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False, unique=True),
        sa.Column("learning_style", sa.String(length=50), nullable=True),
        sa.Column("attention_span_minutes", sa.Integer(), nullable=True),
        sa.Column("best_study_time", sa.String(length=20), nullable=True),
        sa.Column("difficulty_areas", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("strength_areas", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "interest_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False, unique=True),
        sa.Column("interests", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("favorite_subjects", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("hobbies", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("motivators", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("aversions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("grade", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="core"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.UniqueConstraint("slug", "grade", name="uq_subject_slug_grade"),
        sa.UniqueConstraint("slug", name="uq_subject_slug"),
    )

    op.create_table(
        "curriculum_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bncc_code", sa.String(length=50), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("difficulty_level", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="seed_demo"),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "school_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("guardians.id"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("material_type", sa.String(length=50), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=True),
        sa.Column("file_name", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="manual_upload"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "school_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("guardians.id"), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school_materials.id"), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("task_type", sa.String(length=50), nullable=False, server_default="homework"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("due_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("parent_notes", sa.Text(), nullable=True),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "classified_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school_tasks.id"), nullable=False, unique=True),
        sa.Column("curriculum_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("curriculum_items.id"), nullable=True),
        sa.Column("difficulty_assessed", sa.String(length=20), nullable=True),
        sa.Column("estimated_duration", sa.Integer(), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("classification_method", sa.String(length=50), nullable=True),
        sa.Column("classification_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("classified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classified_by", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "study_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("plan_type", sa.String(length=50), nullable=False, server_default="weekly"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("generated_by", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("plan_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "study_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("study_plans.id"), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school_tasks.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_start", sa.Time(), nullable=True),
        sa.Column("scheduled_end", sa.Time(), nullable=True),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "provider_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "provider_sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("provider_accounts.id"), nullable=False),
        sa.Column("sync_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("items_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )

    op.create_table(
        "mary_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_by", sa.String(length=50), nullable=False, server_default="system"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', NOW())")),
    )


def downgrade() -> None:
    for table_name in [
        "mary_reports",
        "provider_sync_logs",
        "provider_accounts",
        "study_sessions",
        "study_plans",
        "classified_tasks",
        "school_tasks",
        "school_materials",
        "curriculum_items",
        "subjects",
        "interest_profiles",
        "student_profiles",
        "students",
        "guardians",
        "families",
    ]:
        op.drop_table(table_name)
