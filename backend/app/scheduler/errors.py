from typing import Literal

InputErrorCode = Literal["duplicate_task_id", "unknown_dependency", "dependency_cycle"]


class ScheduleInputError(ValueError):
    """Rejected input; for ``dependency_cycle``, ``task_ids`` is the loop in dependency order."""

    def __init__(self, code: InputErrorCode, task_ids: tuple[str, ...], message: str) -> None:
        super().__init__(message)
        self.code: InputErrorCode = code
        self.task_ids = task_ids
