"""MySQL script that loads a quarter's tasks into a dondon account (flat tasks in its Inbox).

Pure like the other exporters: ``ExportData`` plus options in, bytes out. The script is meant to
be piped into the ``mysql`` client, which stops at the first error, so a missing user or Inbox
(NULL into a NOT NULL column) leaves the transaction uncommitted.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.exporters.model import ExportData, TaskRow

SQL_MEDIA_TYPE = "application/sql; charset=utf-8"
MAX_TITLE = 500
MIN_DURATION, MAX_DURATION = 15, 1440
# dondon writes ids as 32 hex characters (SQLAlchemy Uuid on MySQL), never with dashes: rows
# written with UUID() are not found when the app binds its own ids.
NEW_ID = "REPLACE(UUID(), '-', '')"
_PRIORITY = {"high": 3, "medium": 2, "low": 1}
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SAFE_EMAIL = re.compile(r"^[^@\s'\"\;`]{1,64}@[^@\s'\"\;`]{1,190}\.[^@\s'\"\;`]{2,63}$")


@dataclass(frozen=True)
class DondonSqlOptions:
    email: str
    tag_name: str
    work_start: time = time(9, 0)
    utc_offset_minutes: int = 420
    map_priority: bool = True
    keep_status: bool = True


def sql_string(value: str) -> str:
    """A MySQL string literal. Backslash and quote are escaped; control characters are dropped
    except tab and newline, which are written as escape sequences."""
    cleaned = _CONTROL.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))
    escaped = cleaned.replace("\\", "\\\\").replace("'", "''")
    return "'" + escaped.replace("\n", "\\n").replace("\t", "\\t") + "'"


def _comment(value: str) -> str:
    """Single-line text that is safe inside a ``--`` comment."""
    return " ".join(_CONTROL.sub("", value).split())


def _utc(day: date, at: time, offset_minutes: int) -> str:
    local = datetime.combine(day, at)
    return (local - timedelta(minutes=offset_minutes)).strftime("%Y-%m-%d %H:%M:%S")


def _literal(value: str | None) -> str:
    return "NULL" if value is None else sql_string(value)


class DondonSqlExporter:
    extension = "sql"
    media_type = SQL_MEDIA_TYPE

    def __init__(self, options: DondonSqlOptions) -> None:
        self.options = options

    def render(self, data: ExportData) -> bytes:
        return "\n".join(self._lines(data)).encode("utf-8")

    def _lines(self, data: ExportData) -> list[str]:
        o = self.options
        email, tag = sql_string(o.email), sql_string(o.tag_name)
        lines = [
            f"-- OKR plan {_comment(data.quarter_label)} -> dondon (MySQL)",
            f"-- Account: {_comment(o.email)} | tag: {_comment(o.tag_name)}"
            f" | {len(data.tasks)} tasks",
            "-- Run with the mysql client (it stops at the first error, so nothing is committed):",
            "--   mysql -u USER -p DONDON_DATABASE < this-file.sql",
            "-- Re-running is safe: a task with the same title and start date in the Inbox that",
            "-- already carries the tag is skipped. Replace COMMIT with ROLLBACK to preview.",
            "SET NAMES utf8mb4;",
            "START TRANSACTION;",
            "",
            f"SET @uid = (SELECT id FROM users WHERE email = {email} LIMIT 1);",
            "SET @sys = (SELECT id FROM folders WHERE user_id = @uid AND is_deleted = 0",
            "  AND (name = '__inbox__' OR LOWER(TRIM(name)) = 'personal')",
            "  ORDER BY (name = '__inbox__') DESC, sort_order, created_at LIMIT 1);",
            "SET @list = (SELECT id FROM lists WHERE folder_id = @sys AND list_type = 'task'",
            "  AND is_deleted = 0 ORDER BY sort_order, created_at LIMIT 1);",
            "SELECT @uid AS user_id, @list AS inbox_list_id;",
            "",
            "UPDATE tags SET is_deleted = 0",
            f"WHERE user_id = @uid AND name = {tag} AND is_deleted = 1;",
            "-- Fails here (NULL user_id) when no dondon account has that email.",
            "INSERT INTO tags (id, user_id, name, color_id, is_deleted)",
            f"SELECT {NEW_ID}, @uid, {tag}, 'red', 0 FROM DUAL",
            f"WHERE NOT EXISTS (SELECT 1 FROM tags WHERE user_id = @uid AND name = {tag});",
            f"SET @tag = (SELECT id FROM tags WHERE user_id = @uid AND name = {tag} LIMIT 1);",
            "",
        ]
        for index, task in enumerate(data.tasks, start=1):
            lines += self._task(index, task)
        lines += [
            "SELECT COUNT(*) AS tasks_with_tag FROM task_tags WHERE tag_id = @tag;",
            "COMMIT;",
            "",
        ]
        return lines

    def _task(self, index: int, task: TaskRow) -> list[str]:
        o = self.options
        title = _comment(task.title)[:MAX_TITLE] or "(untitled)"
        description = f"Objective: {task.objective}\nKR: {task.key_result}"
        if task.done_criteria:
            description += f"\n{task.done_criteria}"
        start = _utc(task.start, o.work_start, o.utc_offset_minutes) if task.start else None
        due = _utc(task.end, time(0, 0), o.utc_offset_minutes) if task.end else None
        done = o.keep_status and task.status == "done"
        status = task.status if o.keep_status else "todo"
        completed = (
            _utc(task.end, o.work_start, o.utc_offset_minutes) if done and task.end else None
        )
        priority = _PRIORITY.get(task.objective_priority, 0) if o.map_priority else 0
        duration = min(MAX_DURATION, max(MIN_DURATION, task.estimate_minutes))
        t = f"@t{index}"
        start_sql, due_sql = _literal(start), _literal(due)
        return [
            f"-- {index}. {_comment(title)}",
            f"SET {t} = {NEW_ID};",
            "INSERT INTO tasks (id, list_id, title, description, due_date, due_has_time,",
            "  start_date, duration_minutes, priority, is_completed, status, completed_at,",
            "  sort_order)",
            f"SELECT {t}, @list, {sql_string(title)}, {sql_string(description)}, {due_sql}, 0,",
            f"  {start_sql}, {duration}, {priority}, {int(done)}, {sql_string(status)},",
            f"  {_literal(completed)}, {index} FROM DUAL",
            "WHERE NOT EXISTS (SELECT 1 FROM tasks x JOIN task_tags tt ON tt.task_id = x.id",
            f"  WHERE x.list_id = @list AND x.is_deleted = 0 AND x.title = {sql_string(title)}",
            f"  AND x.start_date <=> {start_sql} AND tt.tag_id = @tag);",
            "INSERT INTO task_tags (id, task_id, tag_id)",
            f"SELECT {NEW_ID}, id, @tag FROM tasks WHERE id = {t};",
            "",
        ]
