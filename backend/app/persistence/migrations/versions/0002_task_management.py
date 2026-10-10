"""Task management: pinned days, user edits, completion time, inactive objectives,
schedule fingerprint and finished-task history.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-01
"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "task_pins",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint("minutes > 0", name=op.f("ck_task_pins_minutes_positive")),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_task_pins_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "date", name=op.f("pk_task_pins")),
    )
    # Plain ADD COLUMN: a batch rebuild of ``tasks`` on SQLite would cascade-delete child rows.
    op.add_column(
        "tasks", sa.Column("user_edited", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column("tasks", sa.Column("completed_at", TS, nullable=True))
    op.add_column(
        "objectives", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False)
    )
    op.add_column("schedule_runs", sa.Column("input_hash", sa.String(64), nullable=True))
    op.add_column(
        "allocations", sa.Column("done", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    _copy_pins_from_latest_schedule()


def _copy_pins_from_latest_schedule() -> None:
    """Pinned tasks used to keep the days of the latest schedule; store those days explicitly."""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT a.task_id, a.date, a.minutes, t.estimate_minutes "
            "FROM allocations a "
            "JOIN tasks t ON t.id = a.task_id "
            "JOIN schedule_runs r ON r.id = a.schedule_run_id "
            "WHERE t.pinned AND r.id = ("
            "  SELECT max(r2.id) FROM schedule_runs r2 WHERE r2.quarter_id = r.quarter_id"
            ")"
        ).columns(
            sa.column("task_id", sa.Integer),
            sa.column("date", sa.Date),
            sa.column("minutes", sa.Integer),
            sa.column("estimate_minutes", sa.Integer),
        )
    ).all()
    by_task: dict[int, list[tuple[date, int]]] = {}
    estimates: dict[int, int] = {}
    for task_id, day, minutes, estimate in rows:
        by_task.setdefault(task_id, []).append((day, minutes))
        estimates[task_id] = estimate
    kept = sorted(t for t, days in by_task.items() if sum(m for _, m in days) == estimates[t])
    pins = [
        {"task_id": task_id, "date": day, "minutes": minutes}
        for task_id in kept
        for day, minutes in by_task[task_id]
    ]
    if pins:
        meta = sa.MetaData()
        meta.reflect(bind=bind, only=("task_pins",))
        op.bulk_insert(meta.tables["task_pins"], pins)
    unpin = sa.text("UPDATE tasks SET pinned = :off WHERE pinned")
    if kept:
        unpin = sa.text(
            "UPDATE tasks SET pinned = :off WHERE pinned AND id NOT IN :kept"
        ).bindparams(sa.bindparam("kept", expanding=True))
        bind.execute(unpin, {"off": False, "kept": kept})
    else:
        bind.execute(unpin, {"off": False})


def downgrade() -> None:
    op.drop_column("allocations", "done")
    op.drop_column("schedule_runs", "input_hash")
    op.drop_column("objectives", "active")
    op.drop_column("tasks", "completed_at")
    op.drop_column("tasks", "user_edited")
    op.drop_table("task_pins")
