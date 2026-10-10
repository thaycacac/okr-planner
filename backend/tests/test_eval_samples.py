"""The eval OKR samples must stay valid and internally consistent so graders can rely on them."""

import json
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field, model_validator

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "evals" / "okr_samples"
USABLE_HOURS_DEFAULT = 66 * 4 * 0.9


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuarterRef(_Strict):
    year: int = Field(ge=2026, le=2026)
    number: int = Field(ge=1, le=4)


class SampleKeyResult(_Strict):
    id: str
    text: str = Field(min_length=5)
    metric: str | None
    unit: str | None
    baseline: float | None
    target: float | None


class SampleObjective(_Strict):
    id: str
    title: str = Field(min_length=5)
    key_results: list[SampleKeyResult] = Field(min_length=2, max_length=4)


class SampleInput(_Strict):
    objectives: list[SampleObjective] = Field(min_length=1, max_length=3)
    context: str
    clarifications: list[Any] = Field(max_length=0)
    language: Literal["vi", "en"]


class HoursRange(_Strict):
    min: int = Field(ge=2)
    max: int

    @model_validator(mode="after")
    def _ordered(self) -> "HoursRange":
        assert self.min <= self.max
        return self


class KeyResultExpectation(_Strict):
    hours_range: HoursRange
    must_cover: list[str] = Field(min_length=1)


class Expected(_Strict):
    clarify_status: Literal["ok", "needs_clarification"]
    clarification_topics: list[str] = Field(max_length=5)
    total_hours_range: HoursRange | None
    key_results: dict[str, KeyResultExpectation]
    grader_notes: str = Field(min_length=1)


class EvalSample(_Strict):
    schema_version: Literal[1]
    sample_id: str
    domain: str
    quarter: QuarterRef
    kr_kinds: dict[str, Literal["numeric", "qualitative"]]
    input: SampleInput
    expected: Expected

    def key_results(self) -> list[SampleKeyResult]:
        return [kr for obj in self.input.objectives for kr in obj.key_results]


def _sample_paths() -> list[Path]:
    return sorted(SAMPLES_DIR.glob("*.json"))


def _raw(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _load(path: Path) -> EvalSample:
    return EvalSample.model_validate(_raw(path))


def test_there_are_ten_samples() -> None:
    assert len(_sample_paths()) == 10


@pytest.mark.parametrize("path", _sample_paths(), ids=lambda p: p.stem)
def test_sample_is_consistent(path: Path) -> None:
    sample = _load(path)
    assert sample.sample_id == path.stem

    krs = sample.key_results()
    kr_ids = [kr.id for kr in krs]
    assert len(kr_ids) == len(set(kr_ids))
    objective_ids = [obj.id for obj in sample.input.objectives]
    assert len(objective_ids) == len(set(objective_ids))
    assert sorted(sample.kr_kinds) == sorted(kr_ids)
    for kr in krs:
        if sample.kr_kinds[kr.id] == "qualitative":
            assert (kr.metric, kr.unit, kr.baseline, kr.target) == (None, None, None, None)

    expected = sample.expected
    if expected.clarify_status == "needs_clarification":
        assert expected.clarification_topics
        assert expected.total_hours_range is None
        assert expected.key_results == {}
        return

    assert expected.clarification_topics == []
    assert sorted(expected.key_results) == sorted(kr_ids)
    assert set(sample.kr_kinds.values()) == {"numeric", "qualitative"}
    for kr in krs:
        if sample.kr_kinds[kr.id] == "numeric":
            assert None not in (kr.metric, kr.unit, kr.baseline, kr.target)

    total = expected.total_hours_range
    assert total is not None
    assert total.min == sum(e.hours_range.min for e in expected.key_results.values())
    assert total.max == sum(e.hours_range.max for e in expected.key_results.values())
    assert total.max <= USABLE_HOURS_DEFAULT


def test_sample_set_mixes_languages_and_ambiguity() -> None:
    samples = [_load(p) for p in _sample_paths()]
    assert {s.input.language for s in samples} == {"vi", "en"}
    assert len({s.domain for s in samples}) >= 5
    ambiguous = [s for s in samples if s.expected.clarify_status == "needs_clarification"]
    assert len(ambiguous) >= 2


@pytest.mark.parametrize("path", _sample_paths(), ids=lambda p: p.stem)
def test_sample_input_matches_pipeline_input(path: Path) -> None:
    schemas = pytest.importorskip("app.planner_llm.schemas")
    raw_input = _raw(path)["input"]
    parsed = schemas.OkrInput.model_validate(raw_input)
    assert parsed.model_dump(exclude_unset=True) == raw_input


@pytest.mark.parametrize("path", _sample_paths(), ids=lambda p: p.stem)
def test_clear_samples_pass_deterministic_precheck(path: Path) -> None:
    schemas = pytest.importorskip("app.planner_llm.schemas")
    precheck = pytest.importorskip("app.planner_llm.precheck")
    sample = _load(path)
    if sample.expected.clarify_status != "ok":
        pytest.skip("ambiguous sample")
    okr = schemas.OkrInput.model_validate(_raw(path)["input"])
    result = precheck.run_precheck(okr, sample.input.language)
    assert result.issues == []
    assert result.metric_gaps == []
