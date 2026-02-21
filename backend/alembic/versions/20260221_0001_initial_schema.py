"""initial schema

Revision ID: 20260221_0001
Revises:
Create Date: 2026-02-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260221_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signals",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("charger_id", sa.String(length=64), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_signals_charger_id"), "signals", ["charger_id"], unique=False)
    op.create_index(op.f("ix_signals_status"), "signals", ["status"], unique=False)
    op.create_index(op.f("ix_signals_timestamp"), "signals", ["timestamp"], unique=False)

    op.create_table(
        "cases",
        sa.Column("pk", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("charger_id", sa.String(length=64), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("root_cause_tag", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommended_action", sa.String(length=64), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("grid_stress_level", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("uncertainty_reasons", sa.JSON(), nullable=False),
        sa.Column("verification_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("case_id", "mode", name="uq_cases_case_id_mode"),
    )
    op.create_index(op.f("ix_cases_case_id"), "cases", ["case_id"], unique=False)
    op.create_index(op.f("ix_cases_mode"), "cases", ["mode"], unique=False)
    op.create_index(op.f("ix_cases_charger_id"), "cases", ["charger_id"], unique=False)
    op.create_index(op.f("ix_cases_priority_score"), "cases", ["priority_score"], unique=False)
    op.create_index(op.f("ix_cases_recommended_action"), "cases", ["recommended_action"], unique=False)

    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("assigned_team", sa.String(length=64), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id"),
    )
    op.create_index(op.f("ix_work_orders_case_id"), "work_orders", ["case_id"], unique=True)
    op.create_index(op.f("ix_work_orders_state"), "work_orders", ["state"], unique=False)

    op.create_table(
        "verification_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id"),
    )
    op.create_index(op.f("ix_verification_tasks_case_id"), "verification_tasks", ["case_id"], unique=True)
    op.create_index(op.f("ix_verification_tasks_status"), "verification_tasks", ["status"], unique=False)

    op.create_table(
        "verification_outcomes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("result", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_verification_outcomes_case_id"), "verification_outcomes", ["case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_outcomes_case_id"), table_name="verification_outcomes")
    op.drop_table("verification_outcomes")

    op.drop_index(op.f("ix_verification_tasks_status"), table_name="verification_tasks")
    op.drop_index(op.f("ix_verification_tasks_case_id"), table_name="verification_tasks")
    op.drop_table("verification_tasks")

    op.drop_index(op.f("ix_work_orders_state"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_case_id"), table_name="work_orders")
    op.drop_table("work_orders")

    op.drop_index(op.f("ix_cases_recommended_action"), table_name="cases")
    op.drop_index(op.f("ix_cases_priority_score"), table_name="cases")
    op.drop_index(op.f("ix_cases_charger_id"), table_name="cases")
    op.drop_index(op.f("ix_cases_mode"), table_name="cases")
    op.drop_index(op.f("ix_cases_case_id"), table_name="cases")
    op.drop_table("cases")

    op.drop_index(op.f("ix_signals_timestamp"), table_name="signals")
    op.drop_index(op.f("ix_signals_status"), table_name="signals")
    op.drop_index(op.f("ix_signals_charger_id"), table_name="signals")
    op.drop_table("signals")

