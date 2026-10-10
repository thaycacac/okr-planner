"""Initial schema: OKR tree, tasks, calendar, plan and schedule runs; seeds VN holidays.

Revision ID: 0001
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from app.calendar import load_holidays
from app.domain.calendar_config import CalendarConfig

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)


def _pk(table: str, *columns: str) -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint(*columns, name=op.f(f"pk_{table}"))


def _fk(table: str, column: str, target: str, ondelete: str) -> sa.ForeignKeyConstraint:
    ref_table = target.split(".")[0]
    return sa.ForeignKeyConstraint(
        [column], [target], name=op.f(f"fk_{table}_{column}_{ref_table}"), ondelete=ondelete
    )


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("llm_provider", sa.String(10), nullable=True),
        sa.Column("local_base_url", sa.String(500), nullable=True),
        sa.Column("local_model", sa.String(200), nullable=True),
        sa.Column("local_api_style", sa.String(30), nullable=True),
        sa.Column("updated_at", TS, nullable=False),
        _pk("app_settings", "id"),
    )
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("name_vi", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        _pk("holidays", "id"),
        sa.UniqueConstraint("date", name=op.f("uq_holidays_date")),
    )
    op.create_table(
        "leave_days",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(200), nullable=True),
        _pk("leave_days", "id"),
        sa.UniqueConstraint("date", name=op.f("uq_leave_days_date")),
    )
    op.create_table(
        "quarters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.CheckConstraint("number BETWEEN 1 AND 4", name=op.f("ck_quarters_number_range")),
        sa.CheckConstraint("year BETWEEN 2000 AND 2100", name=op.f("ck_quarters_year_range")),
        _pk("quarters", "id"),
        sa.UniqueConstraint("year", "number", name="uq_quarters_year_number"),
    )
    op.create_table(
        "calendar_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=True),
        *(
            sa.Column(f"{day}_minutes", sa.Integer(), nullable=False)
            for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
        ),
        sa.Column("work_saturday", sa.Boolean(), nullable=False),
        sa.Column("work_sunday", sa.Boolean(), nullable=False),
        sa.Column("work_holidays", sa.Boolean(), nullable=False),
        sa.Column("updated_at", TS, nullable=False),
        _fk("calendar_settings", "quarter_id", "quarters.id", "CASCADE"),
        _pk("calendar_settings", "id"),
        sa.UniqueConstraint("quarter_id", name="uq_calendar_settings_quarter_id"),
    )
    op.create_table(
        "objectives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.CheckConstraint(
            "priority IN ('high', 'medium', 'low')", name=op.f("ck_objectives_priority_values")
        ),
        _fk("objectives", "quarter_id", "quarters.id", "CASCADE"),
        _pk("objectives", "id"),
    )
    op.create_index(op.f("ix_objectives_quarter_id"), "objectives", ["quarter_id"])
    op.create_table(
        "plan_runs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("skip_clarification", sa.Boolean(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("language", sa.String(2), nullable=True),
        sa.Column("clarifications", sa.JSON(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(20), nullable=True),
        sa.Column("models", sa.JSON(), nullable=False),
        sa.Column("total_retries", sa.Integer(), nullable=False),
        sa.Column("stage_duration_ms", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("task_count", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        _fk("plan_runs", "parent_id", "plan_runs.id", "SET NULL"),
        _fk("plan_runs", "quarter_id", "quarters.id", "CASCADE"),
        _pk("plan_runs", "id"),
    )
    op.create_index(op.f("ix_plan_runs_quarter_id"), "plan_runs", ["quarter_id"])
    op.create_index(op.f("ix_plan_runs_status"), "plan_runs", ["status"])
    op.create_table(
        "key_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("objective_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("baseline", sa.Float(), nullable=True),
        sa.Column("target", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.CheckConstraint(
            "kind IN ('numeric', 'milestone', 'binary', 'other')",
            name=op.f("ck_key_results_kind_values"),
        ),
        _fk("key_results", "objective_id", "objectives.id", "CASCADE"),
        _pk("key_results", "id"),
    )
    op.create_index(op.f("ix_key_results_objective_id"), "key_results", ["objective_id"])
    op.create_table(
        "schedule_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=False),
        sa.Column("plan_run_id", sa.String(36), nullable=True),
        sa.Column("today", sa.Date(), nullable=False),
        sa.Column("window_start", sa.Date(), nullable=False),
        sa.Column("window_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("demand_minutes", sa.Integer(), nullable=False),
        sa.Column("supply_minutes", sa.Integer(), nullable=False),
        sa.Column("buffered_supply_minutes", sa.Integer(), nullable=False),
        sa.Column("buffer_start", sa.Date(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("unscheduled", sa.JSON(), nullable=False),
        sa.Column("days", sa.JSON(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        _fk("schedule_runs", "plan_run_id", "plan_runs.id", "SET NULL"),
        _fk("schedule_runs", "quarter_id", "quarters.id", "CASCADE"),
        _pk("schedule_runs", "id"),
    )
    op.create_index(op.f("ix_schedule_runs_plan_run_id"), "schedule_runs", ["plan_run_id"])
    op.create_index(op.f("ix_schedule_runs_quarter_id"), "schedule_runs", ["quarter_id"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key_result_id", sa.Integer(), nullable=False),
        sa.Column("plan_run_id", sa.String(36), nullable=True),
        sa.Column("source_key", sa.String(100), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("done_criteria", sa.Text(), nullable=False),
        sa.Column("estimate_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')", name=op.f("ck_tasks_status_values")
        ),
        sa.CheckConstraint("estimate_minutes > 0", name=op.f("ck_tasks_estimate_positive")),
        _fk("tasks", "key_result_id", "key_results.id", "CASCADE"),
        _fk("tasks", "plan_run_id", "plan_runs.id", "SET NULL"),
        _pk("tasks", "id"),
    )
    op.create_index(op.f("ix_tasks_key_result_id"), "tasks", ["key_result_id"])
    op.create_index(op.f("ix_tasks_plan_run_id"), "tasks", ["plan_run_id"])
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_run_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("uses_buffer", sa.Boolean(), nullable=False),
        sa.CheckConstraint("minutes > 0", name=op.f("ck_allocations_minutes_positive")),
        _fk("allocations", "schedule_run_id", "schedule_runs.id", "CASCADE"),
        _fk("allocations", "task_id", "tasks.id", "CASCADE"),
        _pk("allocations", "id"),
        sa.UniqueConstraint(
            "schedule_run_id", "task_id", "date", name="uq_allocations_run_task_date"
        ),
    )
    op.create_index(op.f("ix_allocations_schedule_run_id"), "allocations", ["schedule_run_id"])
    op.create_index(op.f("ix_allocations_task_id"), "allocations", ["task_id"])
    op.create_table(
        "task_dependencies",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("depends_on_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "task_id <> depends_on_id", name=op.f("ck_task_dependencies_no_self_dependency")
        ),
        _fk("task_dependencies", "depends_on_id", "tasks.id", "CASCADE"),
        _fk("task_dependencies", "task_id", "tasks.id", "CASCADE"),
        _pk("task_dependencies", "task_id", "depends_on_id"),
    )
    op.create_index(
        op.f("ix_task_dependencies_depends_on_id"), "task_dependencies", ["depends_on_id"]
    )
    _seed()


def _seed() -> None:
    now = datetime.now(UTC)
    bind = op.get_bind()
    meta = sa.MetaData()
    meta.reflect(bind=bind, only=("app_settings", "calendar_settings", "holidays"))

    op.bulk_insert(meta.tables["app_settings"], [{"id": 1, "updated_at": now}])

    defaults = CalendarConfig()
    days = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    op.bulk_insert(
        meta.tables["calendar_settings"],
        [
            {
                "quarter_id": None,
                **{
                    f"{day}_minutes": minutes
                    for day, minutes in zip(days, defaults.weekday_capacity_minutes, strict=True)
                },
                "work_saturday": defaults.work_saturday,
                "work_sunday": defaults.work_sunday,
                "work_holidays": defaults.work_holidays,
                "updated_at": now,
            }
        ],
    )

    calendar = load_holidays()
    rows = [
        {
            "date": h.date,
            "kind": h.kind,
            "name_vi": h.name_vi,
            "name_en": h.name_en,
            "status": h.status,
            "source": h.source,
        }
        for h in calendar.holidays
    ] + [
        {
            "date": m.date,
            "kind": "makeup_day",
            "name_vi": m.reason_vi,
            "name_en": m.reason_en,
            "status": m.status,
            "source": m.source,
        }
        for m in calendar.makeup_days
    ]
    if rows:
        op.bulk_insert(meta.tables["holidays"], sorted(rows, key=lambda r: r["date"]))


def downgrade() -> None:
    op.drop_index(op.f("ix_task_dependencies_depends_on_id"), table_name="task_dependencies")
    op.drop_table("task_dependencies")
    op.drop_index(op.f("ix_allocations_task_id"), table_name="allocations")
    op.drop_index(op.f("ix_allocations_schedule_run_id"), table_name="allocations")
    op.drop_table("allocations")
    op.drop_index(op.f("ix_tasks_plan_run_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_key_result_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_schedule_runs_quarter_id"), table_name="schedule_runs")
    op.drop_index(op.f("ix_schedule_runs_plan_run_id"), table_name="schedule_runs")
    op.drop_table("schedule_runs")
    op.drop_index(op.f("ix_key_results_objective_id"), table_name="key_results")
    op.drop_table("key_results")
    op.drop_index(op.f("ix_plan_runs_status"), table_name="plan_runs")
    op.drop_index(op.f("ix_plan_runs_quarter_id"), table_name="plan_runs")
    op.drop_table("plan_runs")
    op.drop_index(op.f("ix_objectives_quarter_id"), table_name="objectives")
    op.drop_table("objectives")
    op.drop_table("calendar_settings")
    op.drop_table("quarters")
    op.drop_table("leave_days")
    op.drop_table("holidays")
    op.drop_table("app_settings")
