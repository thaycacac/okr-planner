"""ORM tables. Column types stay portable between SQLite (dev/test) and PostgreSQL."""

import datetime as dt
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Dialect,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.persistence.db import Base


class UTCDateTime(TypeDecorator[datetime]):
    """Always hands out aware UTC datetimes; SQLite drops the offset on storage."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime; use utcnow()")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Quarter(Base):
    __tablename__ = "quarters"
    __table_args__ = (
        UniqueConstraint("year", "number", name="uq_quarters_year_number"),
        CheckConstraint("number BETWEEN 1 AND 4", name="number_range"),
        CheckConstraint("year BETWEEN 2000 AND 2100", name="year_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    number: Mapped[int] = mapped_column(Integer)
    # Earliest day tasks may be scheduled; NULL = the later of today and the quarter start.
    plan_start: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    objectives: Mapped[list["Objective"]] = relationship(
        back_populates="quarter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(Objective.position, Objective.id)",
    )


class Objective(Base):
    __tablename__ = "objectives"
    __table_args__ = (
        CheckConstraint("priority IN ('high', 'medium', 'low')", name="priority_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Inactive objectives keep their tasks but are left out of planning and scheduling.
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    quarter: Mapped[Quarter] = relationship(back_populates="objectives")
    key_results: Mapped[list["KeyResult"]] = relationship(
        back_populates="objective",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(KeyResult.position, KeyResult.id)",
    )


class KeyResult(Base):
    __tablename__ = "key_results"
    __table_args__ = (
        CheckConstraint("kind IN ('numeric', 'milestone', 'binary', 'other')", name="kind_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    objective_id: Mapped[int] = mapped_column(
        ForeignKey("objectives.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(10), default="other")
    baseline: Mapped[float | None] = mapped_column(Float)
    target: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))
    due_date: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # A dropped KR keeps its tasks but is left out of planning and scheduling.
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    objective: Mapped[Objective] = relationship(back_populates="key_results")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="key_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(Task.position, Task.id)",
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (CheckConstraint("task_id <> depends_on_id", name="no_self_dependency"),)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    depends_on_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class TaskPin(Base):
    """A day the user fixed for a task; a pinned task's rows sum to its estimate."""

    __tablename__ = "task_pins"
    __table_args__ = (CheckConstraint("minutes > 0", name="minutes_positive"),)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    minutes: Mapped[int] = mapped_column(Integer)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("estimate_minutes > 0", name="estimate_positive"),
        CheckConstraint("status IN ('todo', 'in_progress', 'done')", name="status_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_result_id: Mapped[int] = mapped_column(
        ForeignKey("key_results.id", ondelete="CASCADE"), index=True
    )
    plan_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_runs.id", ondelete="SET NULL"), index=True
    )
    source_key: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    done_criteria: Mapped[str] = mapped_column(Text, default="")
    estimate_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="todo")
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Created or changed by the user; regenerating the plan keeps such tasks.
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    position: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    key_result: Mapped[KeyResult] = relationship(back_populates="tasks")
    dependencies: Mapped[list[TaskDependency]] = relationship(
        foreign_keys=[TaskDependency.task_id],
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=TaskDependency.depends_on_id,
    )
    pins: Mapped[list[TaskPin]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, order_by=TaskPin.date
    )

    @property
    def depends_on(self) -> list[int]:
        return [d.depends_on_id for d in self.dependencies]

    @property
    def pinned_allocations(self) -> list[TaskPin]:
        return list(self.pins) if self.pinned else []

    @property
    def objective_id(self) -> int:
        return self.key_result.objective_id


class CalendarSettings(Base):
    """``quarter_id`` NULL is the global row (seeded by the migration); others override it."""

    __tablename__ = "calendar_settings"
    __table_args__ = (UniqueConstraint("quarter_id", name="uq_calendar_settings_quarter_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter_id: Mapped[int | None] = mapped_column(ForeignKey("quarters.id", ondelete="CASCADE"))
    mon_minutes: Mapped[int] = mapped_column(Integer)
    tue_minutes: Mapped[int] = mapped_column(Integer)
    wed_minutes: Mapped[int] = mapped_column(Integer)
    thu_minutes: Mapped[int] = mapped_column(Integer)
    fri_minutes: Mapped[int] = mapped_column(Integer)
    sat_minutes: Mapped[int] = mapped_column(Integer)
    sun_minutes: Mapped[int] = mapped_column(Integer)
    work_saturday: Mapped[bool] = mapped_column(Boolean)
    work_sunday: Mapped[bool] = mapped_column(Boolean)
    work_holidays: Mapped[bool] = mapped_column(Boolean)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class Holiday(Base):
    """Seeded from ``app/calendar/data``; ``kind = 'makeup_day'`` marks a working make-up day."""

    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, unique=True)
    kind: Mapped[str] = mapped_column(String(30))
    name_vi: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    source: Mapped[str | None] = mapped_column(String(100))


class LeaveDay(Base):
    __tablename__ = "leave_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, unique=True)
    note: Mapped[str | None] = mapped_column(String(200))


class PlanRun(Base):
    """One pipeline execution; answering clarification questions or resuming a failed run
    starts a child run."""

    __tablename__ = "plan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("plan_runs.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), index=True)
    round: Mapped[int] = mapped_column(Integer, default=1)
    skip_clarification: Mapped[bool] = mapped_column(Boolean, default=False)
    context: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(2))
    clarifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    provider: Mapped[str | None] = mapped_column(String(20))
    models: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    total_retries: Mapped[int] = mapped_column(Integer, default=0)
    stage_duration_ms: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    task_count: Mapped[int] = mapped_column(Integer, default=0)
    # Fingerprint of the pipeline input; a resume is refused once the OKR no longer matches.
    okr_hash: Mapped[str | None] = mapped_column(String(64))
    # Tasks per finished KR (pipeline ids), kept on failure so a resume can reuse them.
    decomposed: Mapped[dict[str, list[dict[str, Any]]] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class ScheduleRun(Base):
    __tablename__ = "schedule_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"), index=True
    )
    plan_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_runs.id", ondelete="SET NULL"), index=True
    )
    today: Mapped[date] = mapped_column(Date)
    window_start: Mapped[date] = mapped_column(Date)
    window_end: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))
    demand_minutes: Mapped[int] = mapped_column(Integer)
    supply_minutes: Mapped[int] = mapped_column(Integer)
    buffered_supply_minutes: Mapped[int] = mapped_column(Integer)
    buffer_start: Mapped[date | None] = mapped_column(Date)
    # Fingerprint of the scheduler input without ``today``; a mismatch means the plan is stale.
    input_hash: Mapped[str | None] = mapped_column(String(64))
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    unscheduled: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    days: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    allocations: Mapped[list["Allocation"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(Allocation.date, Allocation.task_id)",
    )


class Allocation(Base):
    __tablename__ = "allocations"
    __table_args__ = (
        UniqueConstraint("schedule_run_id", "task_id", "date", name="uq_allocations_run_task_date"),
        CheckConstraint("minutes > 0", name="minutes_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schedule_run_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_runs.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    date: Mapped[dt.date] = mapped_column(Date)
    minutes: Mapped[int] = mapped_column(Integer)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    uses_buffer: Mapped[bool] = mapped_column(Boolean, default=False)
    # Past days of a finished task, carried over from the previous run as history.
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


class OptionApplication(Base):
    """Overload options applied in one transaction; ``snapshot`` holds what undo restores."""

    __tablename__ = "option_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    option_ids: Mapped[list[str]] = mapped_column(JSON)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    before: Mapped[dict[str, Any]] = mapped_column(JSON)
    after: Mapped[dict[str, Any]] = mapped_column(JSON)
    effects: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    undone_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class AppSettings(Base):
    """Single row (id = 1); NULL columns fall back to the environment."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    llm_provider: Mapped[str | None] = mapped_column(String(10))
    local_base_url: Mapped[str | None] = mapped_column(String(500))
    local_model: Mapped[str | None] = mapped_column(String(200))
    local_api_style: Mapped[str | None] = mapped_column(String(30))
    # Entered in Settings; stored as-is in the local database and never returned by the API.
    openai_api_key: Mapped[str | None] = mapped_column(String(500))
    gemini_api_key: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
