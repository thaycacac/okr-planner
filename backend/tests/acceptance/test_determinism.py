"""Acceptance criterion 7: the same input and settings give a byte-identical schedule.

Compared as JSON bytes. Only ``created_at`` and ``plan_run_id`` are dropped first: they
identify when and by which run the schedule was stored, not what it contains.
"""

import json
import os
import random
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import Engine

from app.domain.calendar_config import CalendarConfig
from app.persistence.db import create_db_engine
from app.scheduler import ScheduleInput
from tests.acceptance.support import (
    PlanLLM,
    calendar_body,
    create_objective,
    create_quarter,
    plan_quarter,
    reschedule,
)
from tests.api_support import BACKEND_DIR, ApiHarness, migrate
from tests.conftest import TEST_DATABASE_URL, TODAY, _reset_postgres_schema
from tests.scheduler_factories import make_input, make_task

RUN_METADATA = ("created_at", "plan_run_id")
UNEVEN = {"mon": 180, "tue": 240, "wed": 120, "thu": 300, "fri": 240, "sat": 120, "sun": 0}


def schedule_bytes(schedule: dict[str, Any]) -> bytes:
    content = {k: v for k, v in schedule.items() if k not in RUN_METADATA}
    return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode()


@contextmanager
def fresh_engine(tmp_path: Path, name: str) -> Iterator[Engine]:
    if TEST_DATABASE_URL is None:
        engine = create_db_engine(f"sqlite:///{tmp_path / name}.db")
    else:
        engine = create_db_engine(TEST_DATABASE_URL)
        _reset_postgres_schema(engine)
    migrate(engine, "head")
    try:
        yield engine
    finally:
        engine.dispose()


def _plan_from_scratch(engine: Engine) -> bytes:
    with ApiHarness.start(engine, today=TODAY) as api:
        api.provider.handler = PlanLLM(tasks_per_kr=7, hours=5, cross_kr=True)
        response = api.client.put("/settings/calendar", json=calendar_body(UNEVEN, saturday=True))
        assert response.status_code == 200, response.text
        leave = {"start_date": "2026-10-12", "end_date": "2026-10-14"}
        assert api.client.post("/calendar/leave-days", json=leave).status_code == 201
        quarter_id = create_quarter(api)
        for title, priority in (
            ("Tăng trưởng người dùng trả phí", "high"),
            ("Ổn định hạ tầng thanh toán", "medium"),
            ("Hoàn thành luận văn thạc sĩ", "low"),
        ):
            create_objective(
                api,
                quarter_id,
                title,
                priority,
                [f"{title} — kết quả {n}" for n in (1, 2, 3)],
            )
        run = plan_quarter(api, quarter_id)
        response = api.client.get(f"/quarters/{quarter_id}/schedule")
        assert response.status_code == 200
        schedule = response.json()
        assert schedule["plan_run_id"] == run["id"]
        assert schedule["tasks"] and schedule["unscheduled"], "want placed and late tasks"
        return schedule_bytes(schedule)


def test_same_okr_and_settings_on_two_fresh_installs_give_identical_schedule_bytes(
    tmp_path: Path,
) -> None:
    with fresh_engine(tmp_path, "first") as engine:
        first = _plan_from_scratch(engine)
    with fresh_engine(tmp_path, "second") as engine:
        second = _plan_from_scratch(engine)
    assert first == second


def test_rescheduling_an_unchanged_quarter_reproduces_the_schedule_bytes(
    api: ApiHarness,
) -> None:
    api.provider.handler = PlanLLM(tasks_per_kr=6, hours=5, cross_kr=True)
    quarter_id = create_quarter(api)
    create_objective(
        api, quarter_id, "Ra mắt sản phẩm di động", "high", ["Phát hành iOS", "Phát hành Android"]
    )
    plan_quarter(api, quarter_id)
    planned = api.client.get(f"/quarters/{quarter_id}/schedule").json()

    again = reschedule(api, quarter_id)
    third = reschedule(api, quarter_id)
    assert planned["id"] < again["id"] < third["id"]
    strip = {k: v for k, v in planned.items() if k != "id"}
    assert schedule_bytes(strip) == schedule_bytes({k: v for k, v in again.items() if k != "id"})
    assert schedule_bytes(again | {"id": 0}) == schedule_bytes(third | {"id": 0})


RUN_SCHEDULER = (
    "import sys\n"
    "from app.scheduler import ScheduleInput, schedule\n"
    "inp = ScheduleInput.model_validate_json(sys.stdin.read())\n"
    "sys.stdout.write(schedule(inp).model_dump_json())\n"
)


def _scheduler_input(order: str) -> str:
    rng = random.Random(7)
    tasks = []
    for objective in (1, 2, 3):
        for kr in (1, 2):
            previous: list[str] = []
            for n in range(12):
                task_id = f"o{objective}.kr{kr}.t{n}"
                deps = previous[-1:] if n % 3 else []
                tasks.append(
                    make_task(
                        task_id,
                        rng.randint(2, 12) * 30,
                        priority=objective,
                        kr_order=kr,
                        order=n,
                        deps=deps,
                    )
                )
                previous.append(task_id)
    if order == "reversed":
        tasks.reverse()
    elif order == "shuffled":
        random.Random(3).shuffle(tasks)
    calendar = CalendarConfig(
        weekday_capacity_minutes=(240, 180, 240, 120, 300, 90, 0),
        work_saturday=True,
        leave_days=frozenset({date(2026, 10, 20), date(2026, 11, 3)}),
    )
    inp: ScheduleInput = make_input(*tasks, calendar=calendar, holidays={date(2026, 11, 24)})
    return inp.model_dump_json()


def test_scheduler_output_bytes_ignore_process_hash_seed_and_task_order() -> None:
    outputs = set()
    for seed, order in (("0", "given"), ("1", "reversed"), ("4242", "shuffled")):
        result = subprocess.run(
            [sys.executable, "-c", RUN_SCHEDULER],
            input=_scheduler_input(order),
            capture_output=True,
            text=True,
            cwd=BACKEND_DIR,
            env={**os.environ, "PYTHONHASHSEED": seed},
            check=True,
        )
        outputs.add(result.stdout)
    assert len(outputs) == 1
    [output] = outputs
    assert '"unscheduled":[' in output and '"scheduled":[{' in output
