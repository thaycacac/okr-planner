"""Resumable plan runs: OKR fingerprint and the tasks of each decomposed key result.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Plain ADD COLUMN: a batch rebuild of ``plan_runs`` on SQLite would null the plan_run_id
    # of every task and schedule run.
    op.add_column("plan_runs", sa.Column("okr_hash", sa.String(64), nullable=True))
    op.add_column("plan_runs", sa.Column("decomposed", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("plan_runs", "decomposed")
    op.drop_column("plan_runs", "okr_hash")
