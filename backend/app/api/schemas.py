"""Public API contract. Class names are the OpenAPI schema names the frontend generates types from,
so renaming a class is a breaking change. Response fields have no defaults on purpose: that keeps
them ``required`` in the schema and non-optional in the generated TypeScript types.
"""

import datetime as dt
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.calendar_config import MAX_WORKDAY_MINUTES
from app.scheduler.models import UnscheduledReason, WarningCode, WarningLevel

MAX_DAY_MINUTES = MAX_WORKDAY_MINUTES


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- errors ---------------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str = Field(
        description="Stable machine code, e.g. not_found, plan_in_progress, invalid_password, "
        "rate_limited, not_authenticated"
    )
    message: str
    attempts_left: int | None = Field(default=None, ge=0)
    retry_after_seconds: int | None = Field(default=None, ge=0)


class ErrorResponse(BaseModel):
    detail: ErrorDetail


# --- auth -----------------------------------------------------------------------------------


class LoginRequest(_Input):
    password: str = Field(min_length=1, max_length=1024)


class SessionInfo(_Output):
    authenticated: bool


# --- OKR tree -------------------------------------------------------------------------------


class ObjectivePriority(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class KeyResultKind(StrEnum):
    numeric = "numeric"
    milestone = "milestone"
    binary = "binary"
    other = "other"


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class QuarterPlanStartUpdate(_Input):
    """``plan_start`` must fall inside the quarter; ``null`` goes back to "today"."""

    plan_start: date | None


class QuarterCreate(_Input):
    year: int = Field(ge=2000, le=2100)
    number: int = Field(ge=1, le=4)


class KeyResultCreate(_Input):
    text: str = Field(min_length=1, max_length=500)
    kind: KeyResultKind = KeyResultKind.other
    baseline: float | None = None
    target: float | None = None
    unit: str | None = Field(default=None, max_length=50)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=1000)
    position: int | None = Field(default=None, ge=0)


class KeyResultUpdate(_Input):
    """Only the fields present in the body are changed; send ``null`` to clear an optional one."""

    text: str | None = Field(default=None, min_length=1, max_length=500)
    kind: KeyResultKind | None = None
    baseline: float | None = None
    target: float | None = None
    unit: str | None = Field(default=None, max_length=50)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=1000)
    position: int | None = Field(default=None, ge=0)
    active: bool | None = Field(
        default=None, description="Dropped KRs are left out of planning and scheduling"
    )


class ObjectiveCreate(_Input):
    title: str = Field(min_length=1, max_length=300)
    priority: ObjectivePriority = ObjectivePriority.medium
    position: int | None = Field(default=None, ge=0)
    active: bool = True
    key_results: list[KeyResultCreate] = Field(default_factory=list, max_length=10)


class ObjectiveUpdate(_Input):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    priority: ObjectivePriority | None = None
    position: int | None = Field(default=None, ge=0)
    active: bool | None = Field(
        default=None, description="Inactive objectives are left out of planning and scheduling"
    )


class PinnedDay(_Output):
    date: date
    minutes: int


class TaskOut(_Output):
    id: int
    key_result_id: int
    objective_id: int
    title: str
    description: str
    done_criteria: str
    estimate_minutes: int
    status: TaskStatus
    pinned: bool
    pinned_allocations: list[PinnedDay] = Field(
        description="Days fixed by the user; empty unless pinned"
    )
    user_edited: bool = Field(description="Created or changed by the user; kept on regeneration")
    position: int
    depends_on: list[int]
    plan_run_id: str | None
    completed_at: datetime | None


class KeyResultOut(_Output):
    id: int
    objective_id: int
    text: str
    kind: KeyResultKind
    baseline: float | None
    target: float | None
    unit: str | None
    due_date: date | None
    note: str | None
    position: int
    active: bool = Field(description="False once the KR was dropped from the quarter")
    tasks: list[TaskOut]


class ObjectiveOut(_Output):
    id: int
    quarter_id: int
    title: str
    priority: ObjectivePriority
    position: int
    active: bool
    key_results: list[KeyResultOut]


# --- plans ----------------------------------------------------------------------------------


class PlanLanguage(StrEnum):
    vi = "vi"
    en = "en"


class PlanRunStatus(StrEnum):
    queued = "queued"
    running = "running"
    needs_clarification = "needs_clarification"
    invalid_input = "invalid_input"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class PlanStage(StrEnum):
    precheck = "precheck"
    clarify = "clarify"
    decompose = "decompose"
    dedup = "dedup"
    validate = "validate"
    schedule = "schedule"


class PlanEventType(StrEnum):
    progress = "progress"
    end = "end"


class PlanEventStatus(StrEnum):
    started = "started"
    retry = "retry"
    completed = "completed"
    skipped = "skipped"
    failed = "failed"


class PlanFailureCode(StrEnum):
    invalid_llm_output = "invalid_llm_output"
    provider_unavailable = "provider_unavailable"
    internal_validation = "internal_validation"
    schedule_input_error = "schedule_input_error"
    internal_error = "internal_error"
    interrupted = "interrupted"


class QuestionSource(StrEnum):
    precheck = "precheck"
    llm = "llm"


class PlanCreate(_Input):
    quarter_id: int
    context: str | None = Field(default=None, max_length=4000)
    language: PlanLanguage | None = Field(
        default=None, description="Detected from the OKR text when omitted"
    )
    skip_clarification: bool = False


class PlanAnswer(_Input):
    question_id: str = Field(min_length=1)
    answer: str = Field(min_length=1, max_length=1000)


class PlanAnswers(_Input):
    answers: list[PlanAnswer] = Field(max_length=20)
    generate_anyway: bool = Field(
        default=False, description="Skip further clarification rounds and generate tasks"
    )


class PlanJob(BaseModel):
    job_id: str
    quarter_id: int
    parent_id: str | None
    status: PlanRunStatus
    round: int


class PlanEvent(BaseModel):
    """One SSE message of ``GET /plans/{job_id}/events``; ``type = end`` is always the last."""

    seq: int
    type: PlanEventType
    run_status: PlanRunStatus
    stage: PlanStage | None
    status: PlanEventStatus | None
    objective_id: int | None
    key_result_id: int | None
    attempt: int | None
    completed: int | None
    total: int | None
    duration_ms: int | None
    percent: int = Field(ge=0, le=100)


class ClarificationQuestion(BaseModel):
    id: str
    key_result_id: int | None
    question: str
    reason: str
    source: QuestionSource


class ClarificationAnswerOut(BaseModel):
    question_id: str
    key_result_id: int | None
    question: str
    answer: str


class PlanIssue(BaseModel):
    code: str
    message: str
    objective_id: int | None
    key_result_id: int | None


class PlanFailure(BaseModel):
    code: PlanFailureCode
    step: PlanStage | None
    message: str
    provider: str | None
    model: str | None
    objective_id: int | None
    key_result_id: int | None
    attempts: int
    errors: list[str]
    suggestions: list[str]


class PlanStepTrace(BaseModel):
    step: PlanStage
    model: str | None
    objective_id: int | None
    key_result_id: int | None
    attempts: int
    retries: int
    duration_ms: int
    errors: list[str]


class PlanRunDetail(BaseModel):
    id: str
    quarter_id: int
    parent_id: str | None
    status: PlanRunStatus
    round: int
    skip_clarification: bool
    language: PlanLanguage | None
    provider: str | None
    models: dict[str, str] = Field(description="Model used per pipeline step")
    total_retries: int
    stage_duration_ms: dict[str, int]
    duration_ms: int | None
    steps: list[PlanStepTrace]
    questions: list[ClarificationQuestion]
    clarifications: list[ClarificationAnswerOut]
    issues: list[PlanIssue]
    error: PlanFailure | None
    resumable: bool = Field(
        description="``POST /plans/{job_id}/resume`` would continue from the failed step, "
        "reusing the key results already decomposed"
    )
    task_count: int
    schedule_run_id: int | None
    progress: PlanEvent | None = Field(description="Latest progress event while the job runs")
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


# --- quarters -------------------------------------------------------------------------------


class QuarterSummary(BaseModel):
    id: int
    year: int
    number: int
    start_date: date
    end_date: date
    plan_start: date | None = Field(
        description="Earliest day tasks may start; null = the later of today and start_date"
    )
    objective_count: int
    key_result_count: int
    task_count: int
    latest_plan_run_id: str | None
    latest_plan_status: PlanRunStatus | None
    created_at: datetime


class QuarterDetail(QuarterSummary):
    objectives: list[ObjectiveOut]


# --- schedule -------------------------------------------------------------------------------


class FeasibilityStatus(StrEnum):
    green = "green"
    yellow = "yellow"
    red = "red"


class DayOffReason(StrEnum):
    weekend = "weekend"
    holiday = "holiday"
    leave = "leave"
    no_capacity = "no_capacity"


class AllocationOut(BaseModel):
    date: date
    minutes: int


class ScheduledTaskOut(BaseModel):
    task_id: int
    key_result_id: int
    objective_id: int
    start_date: date
    end_date: date
    allocations: list[AllocationOut]
    pinned: bool
    uses_buffer: bool
    done: bool = Field(
        description="Finished task: allocations are its past days, kept as history and "
        "not counted in ScheduleDay.scheduled_minutes"
    )


class UnscheduledTaskOut(BaseModel):
    task_id: int
    key_result_id: int
    objective_id: int
    reason: UnscheduledReason


class ScheduleWarningOut(BaseModel):
    code: WarningCode
    level: WarningLevel
    task_ids: list[int]
    dates: list[date]


class FeasibilityOut(BaseModel):
    """D = demand, S = supply of the window; the buffer is the last 10% of S."""

    status: FeasibilityStatus
    demand_minutes: int
    supply_minutes: int
    buffered_supply_minutes: int
    buffer_start: date | None
    late_task_ids: list[int]
    late_key_result_ids: list[int]
    late_objective_ids: list[int]


class ScheduleDay(BaseModel):
    date: date
    capacity_minutes: int
    scheduled_minutes: int
    is_buffer: bool
    off_reason: DayOffReason | None


class QuarterSchedule(BaseModel):
    id: int
    quarter_id: int
    plan_run_id: str | None
    created_at: datetime
    today: date
    window_start: date
    window_end: date
    feasibility: FeasibilityOut
    tasks: list[ScheduledTaskOut]
    unscheduled: list[UnscheduledTaskOut]
    warnings: list[ScheduleWarningOut]
    days: list[ScheduleDay] = Field(description="Every date of the window, working or not")
    stale: bool = Field(
        description="Tasks, pins, OKRs or the calendar changed since this schedule was made; "
        "POST /quarters/{id}/reschedule to refresh it"
    )


# --- settings -------------------------------------------------------------------------------

DayMinutes = Annotated[int, Field(ge=0, le=MAX_DAY_MINUTES)]


class WeekdayCapacity(_Input):
    """Capacity per weekday in whole minutes (0 = not a working day)."""

    mon: DayMinutes
    tue: DayMinutes
    wed: DayMinutes
    thu: DayMinutes
    fri: DayMinutes
    sat: DayMinutes
    sun: DayMinutes


class CalendarSettings(_Input):
    capacity_minutes: WeekdayCapacity
    work_saturday: bool
    work_sunday: bool
    work_holidays: bool


class LlmProviderName(StrEnum):
    local = "local"
    openai = "openai"
    gemini = "gemini"
    claude = "claude"


class LocalApiStyle(StrEnum):
    ollama = "ollama"
    openai_compatible = "openai_compatible"


def _http_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("must be an http(s) URL")
    return value.rstrip("/")


class LlmSettings(BaseModel):
    provider: LlmProviderName
    local_base_url: str
    local_model: str
    local_api_style: LocalApiStyle
    openai_model: str = Field(description="Read-only, from env")
    openai_api_key_configured: bool = Field(
        description="Read-only; the key itself is never returned"
    )
    openai_api_key_saved: bool = Field(description="The key in use was entered in Settings")
    gemini_api_key_saved: bool = Field(description="The key in use was entered in Settings")
    gemini_model: str = Field(description="Read-only, from env")
    gemini_api_key_configured: bool = Field(
        description="Read-only; the key itself is never returned"
    )
    claude_model: str = Field(description="Read-only, from env")
    claude_cli_available: bool = Field(description="Read-only; the `claude` CLI is on PATH")


class LlmSettingsUpdate(_Input):
    provider: LlmProviderName
    local_base_url: str = Field(min_length=1, max_length=500)
    local_model: str = Field(min_length=1, max_length=200)
    local_api_style: LocalApiStyle
    openai_api_key: str | None = Field(
        default=None,
        max_length=500,
        description="Omit or null keeps the stored key; an empty string removes the saved key",
    )
    gemini_api_key: str | None = Field(default=None, max_length=500, description="Same as openai")

    check_url = field_validator("local_base_url")(_http_url)


class LlmTestRequest(_Input):
    """Tests the values currently in the form, which may not be saved yet."""

    provider: LlmProviderName
    local_base_url: str | None = Field(default=None, max_length=500)
    local_model: str | None = Field(default=None, max_length=200)
    local_api_style: LocalApiStyle | None = None
    openai_api_key: str | None = Field(default=None, max_length=500)
    gemini_api_key: str | None = Field(default=None, max_length=500)

    check_url = field_validator("local_base_url")(_http_url)


class LlmTestErrorCode(StrEnum):
    connection_failed = "connection_failed"
    model_not_found = "model_not_found"
    invalid_json = "invalid_json"
    unauthorized = "unauthorized"
    timeout = "timeout"
    not_configured = "not_configured"
    unknown = "unknown"


class LlmTestResult(BaseModel):
    ok: bool
    provider: LlmProviderName
    model: str
    latency_ms: int | None = Field(ge=0)
    error: str | None
    error_code: LlmTestErrorCode | None
    available_models: list[str]


# --- task editing ---------------------------------------------------------------------------

MAX_TASK_MINUTES = 40 * 60


class TaskCreate(_Input):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=4000)
    done_criteria: str = Field(default="", max_length=4000)
    estimate_minutes: int = Field(ge=1, le=MAX_TASK_MINUTES)
    depends_on: list[int] = Field(default_factory=list, max_length=50)
    position: int | None = Field(default=None, ge=0)


class TaskUpdate(_Input):
    """Only the fields present are changed. ``depends_on`` replaces the whole list;
    ``key_result_id`` moves the task to another KR of the same quarter."""

    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    done_criteria: str | None = Field(default=None, max_length=4000)
    estimate_minutes: int | None = Field(default=None, ge=1, le=MAX_TASK_MINUTES)
    depends_on: list[int] | None = Field(default=None, max_length=50)
    status: TaskStatus | None = None
    position: int | None = Field(default=None, ge=0)
    key_result_id: int | None = None


class PinDay(_Input):
    date: date
    minutes: int = Field(ge=1, le=MAX_DAY_MINUTES)


class TaskPinRequest(_Input):
    """Moves and pins a task. ``start_date`` fills whole working days from that date;
    ``allocations`` sets the days explicitly; neither pins the task where it is scheduled now."""

    start_date: date | None = None
    allocations: list[PinDay] | None = Field(default=None, min_length=1, max_length=92)

    @model_validator(mode="after")
    def _one_way(self) -> Self:
        if self.start_date is not None and self.allocations is not None:
            raise ValueError("send start_date or allocations, not both")
        return self


# --- reschedule -----------------------------------------------------------------------------


class RescheduleAction(StrEnum):
    keep = "keep"
    unpin = "unpin"
    repin = "repin"
    unlink = "unlink"


class PinConflictCode(StrEnum):
    pinned_over_capacity = "pinned_over_capacity"
    pinned_non_working_day = "pinned_non_working_day"
    pinned_overdue = "pinned_overdue"
    pinned_outside_quarter = "pinned_outside_quarter"
    pinned_dependency_conflict = "pinned_dependency_conflict"


class PinResolution(_Input):
    """``keep`` the pin as is; ``unpin`` and schedule automatically; ``repin`` at the earliest
    valid days found by the scheduler; ``unlink`` drops the conflicting dependencies."""

    task_id: int
    action: RescheduleAction


class RescheduleRequest(_Input):
    dry_run: bool = Field(default=False, description="Preview only; nothing is stored")
    resolutions: list[PinResolution] = Field(default_factory=list, max_length=500)


class PinConflict(BaseModel):
    task_id: int = Field(description="The pinned task")
    code: PinConflictCode
    dates: list[date]
    related_task_ids: list[int] = Field(
        description="Other pinned tasks on the same day, or the unfinished dependency"
    )
    capacity_minutes: int | None = Field(description="Capacity of the day (over capacity only)")
    pinned_minutes: int | None = Field(description="Pinned minutes on that day")
    allowed_actions: list[RescheduleAction]
    resolution: RescheduleAction | None


class TaskDateChange(BaseModel):
    """``None`` dates mean the task is not scheduled on that side."""

    task_id: int
    before_start: date | None
    before_end: date | None
    after_start: date | None
    after_end: date | None


class RescheduleResult(BaseModel):
    applied: bool = Field(description="False for a dry run or while a conflict is unresolved")
    conflicts: list[PinConflict]
    unresolved_task_ids: list[int]
    changes: list[TaskDateChange]
    before: FeasibilityOut | None
    after: FeasibilityOut
    before_finish_date: date | None
    after_finish_date: date | None
    schedule: QuarterSchedule | None = Field(description="The stored schedule once applied")


# --- calendar -------------------------------------------------------------------------------


class QuarterCalendar(BaseModel):
    quarter_id: int
    overridden: bool = Field(description="False when the quarter uses the global settings")
    settings: CalendarSettings


class LeaveDaysCreate(_Input):
    """Every working day from ``start_date`` to ``end_date`` (inclusive) becomes a leave day;
    weekends, holidays and existing leave days in the range are skipped."""

    start_date: date
    end_date: date | None = None
    note: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _range(self) -> Self:
        end = self.end_date or self.start_date
        if end < self.start_date:
            raise ValueError("end_date is before start_date")
        if (end - self.start_date).days > 92:
            raise ValueError("a leave range covers at most 93 days")
        return self


class LeaveDayOut(_Output):
    id: int
    date: date
    note: str | None


class HolidayKind(StrEnum):
    public_holiday = "public_holiday"
    compensatory = "compensatory"
    swapped_day_off = "swapped_day_off"
    personal_day_off = "personal_day_off"
    makeup_day = "makeup_day"


class HolidayStatus(StrEnum):
    official = "official"
    provisional = "provisional"


class HolidayCreate(_Input):
    """``makeup_day`` is a working day (e.g. a Saturday worked in exchange for a bridge day)."""

    date: date
    kind: HolidayKind
    name_vi: str = Field(min_length=1, max_length=200)
    name_en: str | None = Field(default=None, min_length=1, max_length=200)
    status: HolidayStatus = HolidayStatus.official


class HolidayUpdate(_Input):
    date: dt.date | None = None
    kind: HolidayKind | None = None
    name_vi: str | None = Field(default=None, min_length=1, max_length=200)
    name_en: str | None = Field(default=None, min_length=1, max_length=200)
    status: HolidayStatus | None = None


class HolidayOut(BaseModel):
    id: int
    date: date
    kind: HolidayKind
    name_vi: str
    name_en: str
    status: HolidayStatus
    source: str | None
    custom: bool = Field(description="Added or edited by the user; reset restores the defaults")


# --- KR milestones --------------------------------------------------------------------------


class MilestoneCheckpoint(BaseModel):
    period_end: date
    completed_minutes: int
    progress: float = Field(ge=0, le=1)
    expected_value: float | None = Field(
        description="baseline + (target - baseline) x progress; null without baseline/target"
    )


class KeyResultMilestones(BaseModel):
    """Expected KR value if tasks finish as scheduled; not a forecast of the outcome."""

    key_result_id: int
    objective_id: int
    kind: KeyResultKind
    baseline: float | None
    target: float | None
    unit: str | None
    total_minutes: int
    planned_minutes: int = Field(description="Minutes done or scheduled inside the quarter")
    expected_completion_date: date | None
    weekly: list[MilestoneCheckpoint]
    monthly: list[MilestoneCheckpoint]


# --- overload options -----------------------------------------------------------------------


class OptionKind(StrEnum):
    weekday_minutes = "weekday_minutes"
    work_saturday = "work_saturday"
    work_sunday = "work_sunday"
    work_holidays = "work_holidays"
    drop_kr = "drop_kr"
    drop_objective = "drop_objective"
    defer_kr = "defer_kr"


class OptionGroup(StrEnum):
    more_time = "more_time"
    less_scope = "less_scope"
    defer = "defer"


class OptionOutcome(BaseModel):
    """One real scheduler run; deltas compare it with the current data without options."""

    feasibility: FeasibilityOut
    finish_date: date | None = Field(description="Last scheduled day")
    late_task_count: int
    shortfall_minutes: int = Field(description="Estimate of the tasks that do not fit")
    buffer_minutes: int = Field(description="Capacity of the buffer days")
    buffer_used_minutes: int = Field(description="Minutes scheduled on buffer days")
    supply_delta_minutes: int
    demand_delta_minutes: int
    resolves_overload: bool = Field(description="No red warning is left")


class OptionEffectCode(StrEnum):
    quarter_calendar_changed = "quarter_calendar_changed"
    key_result_dropped = "key_result_dropped"
    objective_paused = "objective_paused"
    key_result_deferred = "key_result_deferred"


class OptionEffect(BaseModel):
    """What applying changes outside the schedule, for the "will change" summary."""

    option_id: str
    code: OptionEffectCode
    key_result_id: int | None
    objective_id: int | None
    task_count: int = Field(description="Tasks leaving the schedule (0 for calendar changes)")
    pinned_task_ids: list[int] = Field(description="Pinned tasks whose pins are removed")
    calendar: CalendarSettings | None = Field(
        description="Settings of this quarter after the change (calendar options only)"
    )
    target_year: int | None
    target_number: int | None
    target_quarter_exists: bool | None = Field(
        description="False when deferring creates the next quarter"
    )


class OverloadOption(BaseModel):
    id: str = Field(
        description="Stable id: weekday_minutes:+60, work_saturday, work_sunday, work_holidays, "
        "drop_kr:{id}, drop_objective:{id}, defer_kr:{id}"
    )
    kind: OptionKind
    group: OptionGroup
    extra_minutes: int | None = Field(description="Added to every working weekday")
    key_result_id: int | None
    objective_id: int | None
    outcome: OptionOutcome = Field(description="Result of this option on its own")
    conflicts_with: list[str] = Field(description="Listed options that cannot be combined")
    effects: list[OptionEffect]


class WeekdayHint(BaseModel):
    """Binary search over the extra minutes per working weekday, in ``step_minutes`` steps."""

    current_minutes: list[int] = Field(description="Capacity Monday..Friday")
    step_minutes: int
    min_extra_minutes_not_red: int | None = Field(description="Null when 12h/day is not enough")
    min_extra_minutes_green: int | None


class OverloadOptions(BaseModel):
    quarter_id: int
    overloaded: bool = Field(description="The current data has red warnings")
    current: OptionOutcome
    options: list[OverloadOption]
    weekday_hint: WeekdayHint | None


class OptionSelection(_Input):
    option_ids: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(max_length=20)


class OptionEvaluation(BaseModel):
    option_ids: list[str]
    before: OptionOutcome
    after: OptionOutcome
    effects: list[OptionEffect]


class OptionApplication(BaseModel):
    id: int
    quarter_id: int
    option_ids: list[str]
    before: OptionOutcome
    after: OptionOutcome
    effects: list[OptionEffect]
    created_at: datetime
    undone_at: datetime | None
    schedule: QuarterSchedule = Field(description="Latest stored schedule of the quarter")


# --- export ---------------------------------------------------------------------------------


class ExportFormat(StrEnum):
    xlsx = "xlsx"
    csv = "csv"


class ExportSheet(StrEnum):
    tasks = "tasks"
    days = "days"
    weeks = "weeks"
