"""Deterministic scheduler, feasibility and what-if.

Must stay pure: no system clock, DB, network or randomness; depends only on
``app.domain`` and ``app.calendar``.
"""

from app.scheduler.engine import buffer_start_index, schedule
from app.scheduler.errors import ScheduleInputError
from app.scheduler.milestones import Checkpoint, KrMilestones, MilestoneTask, kr_milestones
from app.scheduler.models import (
    Allocation,
    Feasibility,
    ScheduledTask,
    ScheduleInput,
    ScheduleResult,
    SchedulerTask,
    ScheduleWarning,
    UnscheduledTask,
)

__all__ = [
    "Allocation",
    "Checkpoint",
    "Feasibility",
    "KrMilestones",
    "MilestoneTask",
    "ScheduleInput",
    "ScheduleInputError",
    "ScheduleResult",
    "ScheduleWarning",
    "ScheduledTask",
    "SchedulerTask",
    "UnscheduledTask",
    "buffer_start_index",
    "kr_milestones",
    "schedule",
]
