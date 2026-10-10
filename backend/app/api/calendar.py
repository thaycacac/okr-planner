"""Per-quarter calendar override, leave days and the editable holiday list.

Changes never recompute a stored schedule; the affected quarter turns ``stale`` instead.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import Db
from app.api.errors import ApiError, error_responses, not_found
from app.api.schemas import (
    CalendarSettings,
    HolidayCreate,
    HolidayKind,
    HolidayOut,
    HolidayStatus,
    HolidayUpdate,
    LeaveDayOut,
    LeaveDaysCreate,
    QuarterCalendar,
)
from app.api.settings import calendar_schema
from app.calendar import load_holiday_year
from app.domain.quarter import Quarter as QuarterPeriod
from app.persistence.models import CalendarSettings as CalendarSettingsRow
from app.persistence.models import Holiday, LeaveDay, Quarter
from app.services.scheduling import (
    MAKEUP_KIND,
    WEEKDAY_COLUMNS,
    CalendarInputs,
    effective_calendar,
)

router = APIRouter(tags=["calendar"])
NOT_FOUND = error_responses(404)
USER_SOURCE = "user"
Year = Annotated[int | None, Query(ge=2000, le=2100)]


def _quarter(session: Session, quarter_id: int) -> Quarter:
    quarter = session.get(Quarter, quarter_id)
    if quarter is None:
        raise not_found("quarter", quarter_id)
    return quarter


def _override(session: Session, quarter_id: int) -> CalendarSettingsRow | None:
    return session.scalars(
        select(CalendarSettingsRow).where(CalendarSettingsRow.quarter_id == quarter_id)
    ).first()


def _quarter_calendar(session: Session, quarter_id: int) -> QuarterCalendar:
    return QuarterCalendar(
        quarter_id=quarter_id,
        overridden=_override(session, quarter_id) is not None,
        settings=calendar_schema(effective_calendar(session, quarter_id)),
    )


def _year_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


@router.get("/quarters/{quarter_id}/calendar", responses=NOT_FOUND)
def get_quarter_calendar(quarter_id: int, session: Db) -> QuarterCalendar:
    _quarter(session, quarter_id)
    result = _quarter_calendar(session, quarter_id)
    session.commit()
    return result


@router.put("/quarters/{quarter_id}/calendar", responses=NOT_FOUND)
def put_quarter_calendar(quarter_id: int, body: CalendarSettings, session: Db) -> QuarterCalendar:
    """Overrides the global settings for this quarter only."""
    _quarter(session, quarter_id)
    row = _override(session, quarter_id)
    if row is None:
        row = CalendarSettingsRow(quarter_id=quarter_id)
        session.add(row)
    for day in WEEKDAY_COLUMNS:
        setattr(row, f"{day}_minutes", getattr(body.capacity_minutes, day))
    row.work_saturday = body.work_saturday
    row.work_sunday = body.work_sunday
    row.work_holidays = body.work_holidays
    session.flush()
    result = _quarter_calendar(session, quarter_id)
    session.commit()
    return result


@router.delete("/quarters/{quarter_id}/calendar", responses=NOT_FOUND)
def delete_quarter_calendar(quarter_id: int, session: Db) -> QuarterCalendar:
    """Drops the override; the quarter follows the global settings again."""
    _quarter(session, quarter_id)
    session.execute(delete(CalendarSettingsRow).where(CalendarSettingsRow.quarter_id == quarter_id))
    result = _quarter_calendar(session, quarter_id)
    session.commit()
    return result


# --- leave days -----------------------------------------------------------------------------


@router.get("/calendar/leave-days")
def list_leave_days(session: Db, year: Year = None) -> list[LeaveDayOut]:
    query = select(LeaveDay).order_by(LeaveDay.date)
    if year is not None:
        start, end = _year_range(year)
        query = query.where(LeaveDay.date >= start, LeaveDay.date <= end)
    return [LeaveDayOut.model_validate(row) for row in session.scalars(query).all()]


def _period_of(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


@router.post(
    "/calendar/leave-days",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(422),
)
def create_leave_days(body: LeaveDaysCreate, session: Db) -> list[LeaveDayOut]:
    """Returns only the days that were added (possibly none)."""
    end = body.end_date or body.start_date
    calendars: dict[tuple[int, int], CalendarInputs] = {}
    created: list[LeaveDay] = []
    day = body.start_date
    while day <= end:
        span = _period_of(day)
        if span not in calendars:
            year, number = span
            calendars[span] = CalendarInputs(session, QuarterPeriod(year=year, number=number))
        # Capacity is 0 on days off and on days that are already leave days.
        if calendars[span].capacity(day) > 0:
            created.append(LeaveDay(date=day, note=body.note))
        day += timedelta(days=1)
    session.add_all(created)
    session.commit()
    return [LeaveDayOut.model_validate(row) for row in created]


@router.delete(
    "/calendar/leave-days/{leave_day_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_leave_day(leave_day_id: int, session: Db) -> Response:
    row = session.get(LeaveDay, leave_day_id)
    if row is None:
        raise not_found("leave day", leave_day_id)
    session.delete(row)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- holidays -------------------------------------------------------------------------------


def _holiday_out(row: Holiday) -> HolidayOut:
    return HolidayOut(
        id=row.id,
        date=row.date,
        kind=HolidayKind(row.kind),
        name_vi=row.name_vi,
        name_en=row.name_en,
        status=HolidayStatus(row.status),
        source=row.source,
        custom=row.source == USER_SOURCE,
    )


def _holiday(session: Session, holiday_id: int) -> Holiday:
    row = session.get(Holiday, holiday_id)
    if row is None:
        raise not_found("holiday", holiday_id)
    return row


def _ensure_free(session: Session, day: date, holiday_id: int | None = None) -> None:
    existing = session.scalar(select(Holiday.id).where(Holiday.date == day))
    if existing is not None and existing != holiday_id:
        raise ApiError(409, "holiday_exists", f"{day} is already in the holiday list")


@router.get("/calendar/holidays")
def list_holidays(session: Db, year: Year = None) -> list[HolidayOut]:
    query = select(Holiday).order_by(Holiday.date)
    if year is not None:
        start, end = _year_range(year)
        query = query.where(Holiday.date >= start, Holiday.date <= end)
    return [_holiday_out(row) for row in session.scalars(query).all()]


@router.post(
    "/calendar/holidays",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
def create_holiday(body: HolidayCreate, session: Db) -> HolidayOut:
    _ensure_free(session, body.date)
    row = Holiday(
        date=body.date,
        kind=body.kind.value,
        name_vi=body.name_vi.strip(),
        name_en=(body.name_en or body.name_vi).strip(),
        status=body.status.value,
        source=USER_SOURCE,
    )
    session.add(row)
    session.commit()
    return _holiday_out(row)


@router.patch("/calendar/holidays/{holiday_id}", responses=error_responses(404, 409, 422))
def update_holiday(holiday_id: int, body: HolidayUpdate, session: Db) -> HolidayOut:
    row = _holiday(session, holiday_id)
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None:
            raise ApiError(422, "field_required", f"{field} cannot be null")
    if "date" in changes:
        _ensure_free(session, changes["date"], holiday_id)
    for field, value in changes.items():
        setattr(row, field, value.strip() if isinstance(value, str) else value)
    if changes:
        row.source = USER_SOURCE
    session.commit()
    return _holiday_out(row)


@router.delete(
    "/calendar/holidays/{holiday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_holiday(holiday_id: int, session: Db) -> Response:
    session.delete(_holiday(session, holiday_id))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/calendar/holidays/reset", responses=NOT_FOUND)
def reset_holidays(session: Db, year: Annotated[int, Query(ge=2000, le=2100)]) -> list[HolidayOut]:
    """Restores the bundled holiday list of ``year``, dropping every user change in that year."""
    try:
        data = load_holiday_year(year)
    except FileNotFoundError:
        raise ApiError(404, "holiday_data_missing", f"no bundled holidays for {year}") from None
    start, end = _year_range(year)
    session.execute(delete(Holiday).where(Holiday.date >= start, Holiday.date <= end))
    session.add_all(
        [
            Holiday(
                date=h.date,
                kind=h.kind,
                name_vi=h.name_vi,
                name_en=h.name_en,
                status=h.status,
                source=h.source,
            )
            for h in data.holidays
        ]
        + [
            Holiday(
                date=m.date,
                kind=MAKEUP_KIND,
                name_vi=m.reason_vi,
                name_en=m.reason_en,
                status=m.status,
                source=m.source,
            )
            for m in data.makeup_days
        ]
    )
    session.commit()
    return list_holidays(session, year)
