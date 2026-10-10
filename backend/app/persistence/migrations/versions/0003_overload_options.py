"""Overload options: droppable key results and the undo log of applied options.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    # Plain ADD COLUMN: a batch rebuild of ``key_results`` on SQLite would cascade-delete tasks.
    op.add_column(
        "key_results", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False)
    )
    op.create_table(
        "option_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("option_ids", sa.JSON(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("before", sa.JSON(), nullable=False),
        sa.Column("after", sa.JSON(), nullable=False),
        sa.Column("effects", sa.JSON(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("undone_at", TS, nullable=True),
        sa.ForeignKeyConstraint(
            ["quarter_id"],
            ["quarters.id"],
            name=op.f("fk_option_applications_quarter_id_quarters"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_option_applications")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_option_applications_idempotency_key")),
    )
    op.create_index(
        op.f("ix_option_applications_quarter_id"), "option_applications", ["quarter_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_option_applications_quarter_id"), table_name="option_applications")
    op.drop_table("option_applications")
    op.drop_column("key_results", "active")
