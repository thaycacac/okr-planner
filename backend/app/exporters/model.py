"""Export data and the three tables every format writes: tasks, daily schedule, weekly workload.

Both exporters serialize the same ``Table`` values, so CSV and XLSX always carry the same numbers.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.exporters.labels import LABELS, Language

SheetName = Literal["tasks", "days", "weeks"]
SHEETS: tuple[SheetName, ...] = ("tasks", "days", "weeks")
Cell = str | int | float | date | None
# Spreadsheet apps run cells starting with these as formulas (CSV/formula injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


@dataclass(frozen=True)
class TaskRow:
    task_id: int
    objective: str
    key_result: str
    title: str
    estimate_minutes: int
    status: str
    pinned: bool
    start: date | None
    end: date | None
    scheduled_minutes: int
    uses_buffer: bool
    late_reason: str | None
    done_criteria: str
    depends_on: tuple[int, ...]


@dataclass(frozen=True)
class DayRow:
    """``objective_minutes`` follows ``ExportData.objectives``; ``tasks`` is (title, minutes)."""

    date: date
    capacity_minutes: int
    scheduled_minutes: int
    is_buffer: bool
    off_reason: str | None
    tasks: tuple[tuple[str, int], ...]
    objective_minutes: tuple[int, ...]


@dataclass(frozen=True)
class ExportData:
    quarter_label: str
    language: Language
    objectives: tuple[str, ...]
    tasks: tuple[TaskRow, ...]
    days: tuple[DayRow, ...]
    details: bool = False


@dataclass(frozen=True)
class Table:
    sheet: SheetName
    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[Cell, ...], ...]


def hours(minutes: int) -> float:
    return round(minutes / 60, 2)


def text(value: str) -> str:
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def _task_table(data: ExportData) -> Table:
    labels = LABELS[data.language]
    headers = [
        labels["id"],
        labels["objective"],
        labels["key_result"],
        labels["task"],
        labels["estimate_h"],
        labels["status"],
        labels["pinned"],
        labels["start"],
        labels["end"],
        labels["scheduled_h"],
        labels["uses_buffer"],
        labels["not_scheduled"],
    ]
    if data.details:
        headers += [labels["done_criteria"], labels["depends_on"]]
    rows = []
    for task in data.tasks:
        row: list[Cell] = [
            task.task_id,
            text(task.objective),
            text(task.key_result),
            text(task.title),
            hours(task.estimate_minutes),
            labels[f"status_{task.status}"],
            labels["yes"] if task.pinned else labels["no"],
            task.start,
            task.end,
            hours(task.scheduled_minutes),
            labels["yes"] if task.uses_buffer else labels["no"],
            labels[f"late_{task.late_reason}"] if task.late_reason else None,
        ]
        if data.details:
            row += [text(task.done_criteria), ", ".join(str(d) for d in task.depends_on)]
        rows.append(tuple(row))
    return Table("tasks", labels["sheet_tasks"], tuple(headers), tuple(rows))


def _day_table(data: ExportData) -> Table:
    labels = LABELS[data.language]
    headers = (
        labels["date"],
        labels["weekday"],
        labels["capacity_h"],
        labels["scheduled_h"],
        labels["free_h"],
        labels["buffer"],
        labels["day_off"],
        labels["tasks"],
    )
    rows = tuple(
        (
            day.date,
            labels[f"weekday_{day.date.weekday()}"],
            hours(day.capacity_minutes),
            hours(day.scheduled_minutes),
            hours(max(0, day.capacity_minutes - day.scheduled_minutes)),
            labels["yes"] if day.is_buffer else labels["no"],
            labels[f"off_{day.off_reason}"] if day.off_reason else None,
            text("; ".join(f"{title} ({hours(minutes):g}h)" for title, minutes in day.tasks)),
        )
        for day in data.days
    )
    return Table("days", labels["sheet_days"], headers, rows)


def _week_table(data: ExportData) -> Table:
    labels = LABELS[data.language]
    headers = (
        labels["week"],
        labels["start"],
        labels["end"],
        labels["working_days"],
        labels["capacity_h"],
        labels["scheduled_h"],
        labels["utilization"],
        *(text(title) for title in data.objectives),
    )
    weeks: dict[tuple[int, int], list[DayRow]] = {}
    for day in data.days:
        iso = day.date.isocalendar()
        weeks.setdefault((iso.year, iso.week), []).append(day)
    rows = []
    for (_, week), days in weeks.items():
        capacity = sum(d.capacity_minutes for d in days)
        scheduled = sum(d.scheduled_minutes for d in days)
        per_objective = [
            hours(sum(d.objective_minutes[i] for d in days)) for i in range(len(data.objectives))
        ]
        rows.append(
            (
                f"{labels['week_prefix']}{week}",
                days[0].date,
                days[-1].date,
                sum(1 for d in days if d.capacity_minutes > 0),
                hours(capacity),
                hours(scheduled),
                round(scheduled * 100 / capacity, 1) if capacity else None,
                *per_objective,
            )
        )
    return Table("weeks", labels["sheet_weeks"], headers, tuple(rows))


def tables(data: ExportData, sheets: Sequence[SheetName] = SHEETS) -> list[Table]:
    builders = {"tasks": _task_table, "days": _day_table, "weeks": _week_table}
    return [builders[sheet](data) for sheet in sheets]
