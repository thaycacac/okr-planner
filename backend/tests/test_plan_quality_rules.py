import pytest

from app.planner_llm.schemas import LLMTask
from app.planner_llm.validation import (
    kr_hours_cap,
    kr_hours_errors,
    numbered_sibling_errors,
    part_title_errors,
    plan_quality_errors,
    rebalance_caps,
    task_quality_errors,
    unverifiable_done_criteria_errors,
)


def _task(
    title: str,
    done: str = "Checklist approved by the team lead",
    *,
    local_id: str = "t1",
    hours: float = 4,
    kr_id: str = "kr1",
) -> LLMTask:
    return LLMTask(
        local_id=local_id,
        title=title,
        description="",
        estimate_hours=hours,
        done_criteria=done,
        depends_on=[],
        kr_id=kr_id,
    )


@pytest.mark.parametrize(
    "title",
    [
        "Implement rating improvement strategies part 1",
        "Implement the fix: Part 2",
        "Thực hiện cải thiện uptime phần 1",
        "Viết runbook phần hai",
        "Write the onboarding guide (2/3)",
        "Viết tài liệu hướng dẫn 1/2",
        "Draft the proposal 1 of 3",
    ],
)
def test_part_titles_are_rejected(title: str) -> None:
    (error,) = part_title_errors([_task(title)])
    assert error.startswith("task t1: title is numbered as a part")


@pytest.mark.parametrize(
    "title",
    [
        "Calls 1-3",
        "Gọi khách hàng 4-6",
        "Set up 24/7 on-call monitoring",
        "Cài đặt phần mềm giám sát",
        "Chạy thử phần thanh toán trên staging",
        "Read the paper on part-of-speech tagging",
    ],
)
def test_titles_without_part_numbers_pass(title: str) -> None:
    assert part_title_errors([_task(title)]) == []


@pytest.mark.parametrize(
    "titles",
    [
        ("Implement onboarding improvement 1", "Implement onboarding improvement 2"),
        ("Tối ưu truy vấn thanh toán 1", "Tối ưu truy vấn thanh toán 2"),
        ("Tối ưu truy vấn thanh toán số 1", "Tối Ưu Truy Vấn Thanh Toán số 2"),
        ("Monitor and adjust #1", "Monitor and adjust #2"),
    ],
)
def test_tasks_differing_only_by_a_trailing_number_are_rejected(titles: tuple[str, str]) -> None:
    tasks = [_task(titles[0], local_id="t1"), _task(titles[1], local_id="t2")]

    (error,) = numbered_sibling_errors(tasks)

    assert error.startswith("tasks t1, t2 differ only by a trailing number")


@pytest.mark.parametrize(
    "titles",
    [
        ("Interview customers batch 1", "Interview customers batch 2"),
        ("Phỏng vấn khách hàng đợt 1", "Phỏng vấn khách hàng đợt 2"),
        ("Calls 1-3", "Calls 4-6"),
        ("Thi thử lần 1", "Thi thử lần 2"),
        ("Launch pricing experiment variant 1", "Launch pricing experiment variant 2"),
        ("Thử nghiệm giá phương án 1", "Thử nghiệm giá phương án 2"),
        ("Task t1", "Task t2"),
    ],
)
def test_numbered_batches_and_ranges_pass(titles: tuple[str, str]) -> None:
    tasks = [_task(titles[0], local_id="t1"), _task(titles[1], local_id="t2")]
    assert numbered_sibling_errors(tasks) == []


def test_same_numbered_title_in_different_key_results_passes() -> None:
    tasks = [
        _task("Review progress 1", local_id="kr1.t1", kr_id="kr1"),
        _task("Review progress 2", local_id="kr2.t1", kr_id="kr2"),
    ]
    assert numbered_sibling_errors(tasks) == []


@pytest.mark.parametrize(
    ("title", "done"),
    [
        ("Implement rating improvement strategies", "Rating improvement strategies implemented"),
        ("Revise the pricing strategy", "Strategy revised and finalized"),
        ("Monitor and adjust the campaign", "Adjustments made as needed"),
        ("Review the plan", "Done"),
        ("Tối ưu truy vấn thanh toán", "Đã được tối ưu"),
        ("Cải thiện uptime dịch vụ", "Uptime ổn định hơn"),
        ("Đánh giá và điều chỉnh kế hoạch", "Kế hoạch đã được điều chỉnh nếu cần"),
        ("Viết tài liệu hướng dẫn", "Hoàn thành tài liệu hướng dẫn"),
    ],
)
def test_done_criteria_that_echo_the_title_or_are_generic_are_rejected(
    title: str, done: str
) -> None:
    (error,) = unverifiable_done_criteria_errors([_task(title, done)])
    assert error.startswith("task t1: done_criteria only repeats the title")


@pytest.mark.parametrize(
    ("title", "done"),
    [
        ("Write the runbook for 5 incidents", "Runbook for 5 incidents merged and approved"),
        ("Measure baseline activation rate", "Baseline activation rate logged in the dashboard"),
        ("Improve checkout conversion", "Conversion rises from 2% to 3% in the weekly report"),
        ("Reviewed and merged", "Reviewed and merged by the tech lead"),
        ("Đo thời gian chạy 5 km ban đầu", "Kết quả baseline lưu trong Google Sheet"),
        ("Cải thiện tỉ lệ kích hoạt", "Tỉ lệ kích hoạt đạt 40% trên dashboard"),
        ("Lập thực đơn 4 tuần", "Thực đơn gửi chuyên gia dinh dưỡng và được góp ý bằng văn bản"),
    ],
)
def test_observable_done_criteria_pass(title: str, done: str) -> None:
    assert unverifiable_done_criteria_errors([_task(title, done)]) == []


def test_quality_rules_can_be_switched_off() -> None:
    padded = [_task("Implement the fix part 1", "Fix implemented")]

    assert len(task_quality_errors(padded)) == 2
    assert task_quality_errors(padded, rules={}) == []


def test_key_result_hours_above_the_cap_are_rejected() -> None:
    tasks = [_task("Build the import", local_id="t1", hours=6), _task("Test it", hours=5)]

    assert kr_hours_errors(tasks, 11) == []
    (error,) = kr_hours_errors(tasks, 8)
    assert error.startswith("estimates add up to 11 hours, above the 8 hours")
    assert "cut at least 3 hours" in error
    assert plan_quality_errors(tasks, None) == []
    assert plan_quality_errors(tasks, 8) == [error]


def test_key_result_cap_allows_a_heavy_key_result_but_not_the_whole_quarter() -> None:
    assert kr_hours_cap(117.0, 3) == 58
    assert kr_hours_cap(234.0, 6) == 58
    assert kr_hours_cap(100.0, 1) == 100
    assert kr_hours_cap(3.0, 5) == 2


def test_rebalance_cuts_only_key_results_above_an_equal_share() -> None:
    hours = {"kr1": 70.0, "kr2": 55.0, "kr3": 30.0}

    caps = rebalance_caps(hours, 117.0)

    assert caps == {"kr1": 44.0, "kr2": 42.0}
    assert sum(caps.values()) + hours["kr3"] <= 117.0


def test_rebalance_is_empty_when_the_plan_fits() -> None:
    assert rebalance_caps({"kr1": 60.0, "kr2": 50.0}, 117.0) == {}
    assert rebalance_caps({}, 117.0) == {}
