from datetime import UTC, date, datetime

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, MetaData, inspect, select

from app.calendar import load_holidays
from app.persistence import models
from app.persistence.db import Base
from tests.api_support import migrate


def test_upgrade_matches_models_and_downgrade_removes_everything(empty_engine: Engine) -> None:
    engine = empty_engine
    migrate(engine, "head")

    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []

    migrate(engine, "base", down=True)
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}

    migrate(engine, "head")
    assert "plan_runs" in inspect(engine).get_table_names()


def test_existing_pins_move_to_their_own_table(empty_engine: Engine) -> None:
    """A pinned task keeps its latest scheduled days; one without a full schedule is unpinned."""
    engine = empty_engine
    migrate(engine, "0001")
    now = datetime(2026, 10, 1, tzinfo=UTC)
    meta = MetaData()
    meta.reflect(bind=engine)
    t = meta.tables
    with engine.begin() as connection:

        def insert(table: str, **values: object) -> int:
            result = connection.execute(t[table].insert().values(**values))
            return int(result.inserted_primary_key[0])

        quarter = insert("quarters", year=2026, number=4, created_at=now)
        objective = insert(
            "objectives", quarter_id=quarter, title="O", priority="high", position=0, created_at=now
        )
        kr = insert(
            "key_results",
            objective_id=objective,
            text="KR",
            kind="binary",
            position=0,
            created_at=now,
        )
        task = {
            "key_result_id": kr,
            "title": "T",
            "description": "",
            "done_criteria": "",
            "status": "todo",
            "pinned": True,
            "position": 0,
            "created_at": now,
        }
        full = insert("tasks", estimate_minutes=300, **task)
        partial = insert("tasks", estimate_minutes=600, **task)
        run = {
            "quarter_id": quarter,
            "today": date(2026, 10, 1),
            "window_start": date(2026, 10, 1),
            "window_end": date(2026, 12, 31),
            "status": "green",
            "demand_minutes": 900,
            "supply_minutes": 900,
            "buffered_supply_minutes": 810,
            "warnings": [],
            "unscheduled": [],
            "days": [],
            "created_at": now,
        }
        old_run = insert("schedule_runs", **run)
        latest = insert("schedule_runs", **run)
        allocation = {"pinned": True, "uses_buffer": False}
        insert(
            "allocations",
            schedule_run_id=old_run,
            task_id=partial,
            date=date(2026, 10, 1),
            minutes=600,
            **allocation,
        )
        for run_id, day, minutes in (
            (latest, date(2026, 10, 1), 240),
            (latest, date(2026, 10, 2), 60),
        ):
            insert(
                "allocations",
                schedule_run_id=run_id,
                task_id=full,
                date=day,
                minutes=minutes,
                **allocation,
            )
        insert(
            "allocations",
            schedule_run_id=latest,
            task_id=partial,
            date=date(2026, 10, 5),
            minutes=240,
            **allocation,
        )

    migrate(engine, "head")
    with engine.connect() as connection:
        pins = connection.execute(
            select(models.TaskPin.task_id, models.TaskPin.date, models.TaskPin.minutes).order_by(
                models.TaskPin.date
            )
        ).all()
        pinned = dict(connection.execute(select(models.Task.id, models.Task.pinned)).all())
    assert pins == [(full, date(2026, 10, 1), 240), (full, date(2026, 10, 2), 60)]
    assert pinned == {full: True, partial: False}


def test_seeds_holidays_and_default_settings(db_engine: Engine) -> None:
    engine = db_engine
    calendar = load_holidays()

    with engine.connect() as connection:
        holidays = connection.execute(select(models.Holiday.date, models.Holiday.kind)).all()
        calendar_rows = connection.execute(select(models.CalendarSettings)).all()
        app_rows = connection.execute(select(models.AppSettings.id)).all()

    assert {d for d, kind in holidays if kind != "makeup_day"} == calendar.holiday_dates
    assert {d for d, kind in holidays if kind == "makeup_day"} == calendar.makeup_dates
    assert len(calendar_rows) == 1
    assert calendar_rows[0].quarter_id is None
    assert app_rows == [(1,)]
