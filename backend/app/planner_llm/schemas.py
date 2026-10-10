"""Pipeline input, LLM output and result models.

LLM output models carry no defaults or constraints on purpose: strict Structured Outputs
rejects ``default`` and some local runtimes ignore numeric bounds. Rules are enforced in
``validation`` so the model receives a precise error message on retry.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.planner_llm.providers.base import ProviderName

Language = Literal["vi", "en"]
StageName = Literal["precheck", "clarify", "decompose", "dedup", "validate"]


class KeyResultInput(BaseModel):
    id: str = Field(min_length=1)
    text: str
    metric: str | None = None
    unit: str | None = None
    baseline: float | None = None
    target: float | None = None


class ObjectiveInput(BaseModel):
    id: str = Field(min_length=1)
    title: str
    key_results: list[KeyResultInput] = Field(default_factory=list)


class ClarificationAnswer(BaseModel):
    question: str
    answer: str
    kr_id: str | None = None


class OkrInput(BaseModel):
    objectives: list[ObjectiveInput] = Field(default_factory=list)
    context: str | None = None
    clarifications: list[ClarificationAnswer] = Field(default_factory=list)
    language: Language | None = None


# The scheduler keeps the last 10% of the quarter's supply as buffer.
SCHEDULE_BUFFER_SHARE = 0.1


class TimeBudget(BaseModel):
    """Working time left in the quarter, taken from the calendar so the model never computes it."""

    working_days: int = Field(gt=0)
    total_hours: float = Field(gt=0)

    @property
    def hours_per_day(self) -> float:
        return round(self.total_hours / self.working_days, 1)

    @property
    def usable_hours(self) -> float:
        return round(self.total_hours * (1 - SCHEDULE_BUFFER_SHARE), 1)


class ClarifyQuestionOut(BaseModel):
    kr_id: str | None
    question: str
    reason: str


class KeyResultCheck(BaseModel):
    """``end_result`` comes first so the model quotes the key result before judging it."""

    end_result: str
    concrete: bool


class ClarifyOutput(BaseModel):
    status: Literal["ok", "needs_clarification"]
    questions: list[ClarifyQuestionOut]


class LLMTask(BaseModel):
    local_id: str
    title: str
    description: str
    estimate_hours: float
    done_criteria: str
    depends_on: list[str]
    kr_id: str

    @field_validator("local_id", "kr_id")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()

    @field_validator("depends_on")
    @classmethod
    def _drop_blank_dependencies(cls, value: list[str]) -> list[str]:
        """Small local models often emit ``[""]`` for "no dependency"."""
        return [v.strip() for v in value if v.strip()]


class DecomposeOutput(BaseModel):
    tasks: list[LLMTask]


class TaskMerge(BaseModel):
    keep_id: str
    remove_ids: list[str]


class CrossDependency(BaseModel):
    task_id: str
    depends_on_id: str


class DedupOutput(BaseModel):
    merges: list[TaskMerge]
    cross_dependencies: list[CrossDependency]


class KeyResultNeed(BaseModel):
    kr_id: str
    needs_kr_id: str
    output: str


class KeyResultNeedsOutput(BaseModel):
    needs: list[KeyResultNeed]


class LinkOutput(BaseModel):
    links: list[CrossDependency]


class ClarifyQuestion(BaseModel):
    id: str
    kr_id: str | None
    question: str
    reason: str
    source: Literal["precheck", "llm"]


class PrecheckIssue(BaseModel):
    code: str
    message: str
    objective_id: str | None = None
    kr_id: str | None = None


class PlannedTask(BaseModel):
    """Final task; ``local_id`` is unique across the whole plan."""

    local_id: str
    objective_id: str
    kr_id: str
    title: str
    description: str
    estimate_hours: float
    done_criteria: str
    depends_on: list[str]


class StepTrace(BaseModel):
    step: StageName
    model: str | None = None
    objective_id: str | None = None
    kr_id: str | None = None
    attempts: int = 0
    retries: int = 0
    duration_ms: int = 0
    errors: list[str] = Field(default_factory=list)


class RunTrace(BaseModel):
    provider: ProviderName
    models: dict[str, str]
    total_retries: int
    stage_duration_ms: dict[str, int]
    duration_ms: int
    steps: list[StepTrace]


class PipelineResult(BaseModel):
    status: Literal["ok", "needs_clarification", "invalid_input"]
    language: Language
    questions: list[ClarifyQuestion] = Field(default_factory=list)
    issues: list[PrecheckIssue] = Field(default_factory=list)
    tasks: list[PlannedTask] = Field(default_factory=list)
    trace: RunTrace


FailureCode = Literal["invalid_llm_output", "provider_unavailable", "internal_validation"]
Suggestion = Literal["switch_provider", "switch_model", "check_connection"]


class PipelineFailure(BaseModel):
    code: FailureCode
    step: StageName
    message: str
    provider: ProviderName
    model: str | None = None
    objective_id: str | None = None
    kr_id: str | None = None
    attempts: int = 0
    errors: list[str] = Field(default_factory=list)
    suggestions: list[Suggestion] = Field(default_factory=list)


class ProgressEvent(BaseModel):
    """Progress for SSE; carries ids and counters only, never OKR text."""

    stage: StageName
    status: Literal["started", "retry", "completed", "skipped", "failed"]
    objective_id: str | None = None
    kr_id: str | None = None
    attempt: int | None = None
    completed: int | None = None
    total: int | None = None
    duration_ms: int | None = None


class PipelineError(Exception):
    def __init__(self, failure: PipelineFailure, trace: RunTrace) -> None:
        super().__init__(f"{failure.code} at {failure.step}: {failure.message}")
        self.failure = failure
        self.trace = trace
