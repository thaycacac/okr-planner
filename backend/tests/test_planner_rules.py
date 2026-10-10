import pytest

from app.planner_llm.language import detect_language
from app.planner_llm.precheck import metric_gap, run_precheck
from app.planner_llm.providers.base import parse_json_object
from app.planner_llm.providers.errors import InvalidJSONError
from app.planner_llm.schemas import KeyResultInput, ObjectiveInput, OkrInput
from app.planner_llm.validation import find_cycle


def _okr(title: str, *krs: str) -> OkrInput:
    return OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title=title,
                key_results=[KeyResultInput(id=f"kr{i}", text=t) for i, t in enumerate(krs, 1)],
            )
        ]
    )


def test_find_cycle_returns_closed_path() -> None:
    assert find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]
    assert find_cycle({"a": ["a"]}) == ["a", "a"]


def test_find_cycle_accepts_dag_and_ignores_unknown_edges() -> None:
    assert find_cycle({"a": [], "b": ["a"], "c": ["a", "b", "zzz"]}) is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Increase conversion from 2% to 3%", None),
        ("Tăng NPS lên 50", "baseline"),
        ("Giảm thời gian phản hồi khách hàng", "baseline"),
        ("Ship three onboarding improvements", None),
        ("Reach 1000 weekly active users", None),
    ],
)
def test_metric_gap_heuristics(text: str, expected: str | None) -> None:
    gap = metric_gap(KeyResultInput(id="kr1", text=text), "vi")
    if expected is None:
        assert gap is None
    else:
        assert gap is not None
        assert expected in gap.question


def test_structured_metric_needs_baseline_and_target() -> None:
    kr = KeyResultInput(id="kr1", text="Weekly active users", metric="WAU", target=500)
    gap = metric_gap(kr, "en")
    assert gap is not None
    assert "baseline" in gap.question
    assert metric_gap(kr.model_copy(update={"baseline": 200}), "en") is None


def test_precheck_reports_lengths_and_duplicate_ids() -> None:
    okr = OkrInput(
        objectives=[
            ObjectiveInput(
                id="o1",
                title="x" * 301,
                key_results=[
                    KeyResultInput(id="kr1", text="ok"),
                    KeyResultInput(id="kr1", text="A valid key result text"),
                ],
            ),
            ObjectiveInput(id="o2", title="Second objective", key_results=[]),
        ]
    )
    codes = [i.code for i in run_precheck(okr, "en").issues]
    assert codes == ["objective_too_long", "kr_too_short", "duplicate_id", "no_key_results"]


def test_detect_language() -> None:
    assert detect_language(_okr("Nâng cao chất lượng sản phẩm", "Phát hành bản mới")) == "vi"
    assert detect_language(_okr("Improve product quality", "Ship the new release")) == "en"


def test_parse_json_object_tolerates_think_block_and_fence() -> None:
    assert parse_json_object('<think>hmm</think>\n```json\n{"ok": true}\n```') == {"ok": True}


@pytest.mark.parametrize("content", [None, "", "[1, 2]", '{"ok": tru'])
def test_parse_json_object_rejects_non_objects(content: str | None) -> None:
    with pytest.raises(InvalidJSONError):
        parse_json_object(content)
