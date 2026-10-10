"""Editable holiday data files (``data/<country>_holidays_<year>.json``) and their loader."""

from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

DATA_DIR = Path(__file__).resolve().parent / "data"

HolidayKind = Literal["public_holiday", "compensatory", "swapped_day_off"]
EntryStatus = Literal["official", "provisional"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Source(_Frozen):
    id: str
    title: str
    url: str


class Holiday(_Frozen):
    date: date
    name_vi: str
    name_en: str
    kind: HolidayKind
    status: EntryStatus
    source: str


class MakeupDay(_Frozen):
    date: date
    reason_vi: str
    reason_en: str
    status: EntryStatus
    source: str


class HolidayYear(_Frozen):
    """One data file. Validation rejects entries that would silently skew the calendar."""

    country: str
    year: int
    audience: str
    notes: tuple[str, ...] = ()
    sources: tuple[Source, ...]
    holidays: tuple[Holiday, ...]
    makeup_days: tuple[MakeupDay, ...] = ()

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        source_ids = {s.id for s in self.sources}
        entries: list[Holiday | MakeupDay] = [*self.holidays, *self.makeup_days]
        for entry in entries:
            if entry.date.year != self.year:
                raise ValueError(f"{entry.date} does not belong to year {self.year}")
            if entry.source not in source_ids:
                raise ValueError(f"{entry.date} references unknown source {entry.source!r}")
        holiday_dates = [h.date for h in self.holidays]
        if len(holiday_dates) != len(set(holiday_dates)):
            raise ValueError("duplicate holiday dates")
        makeup_dates = [m.date for m in self.makeup_days]
        if len(makeup_dates) != len(set(makeup_dates)):
            raise ValueError("duplicate make-up dates")
        clash = set(holiday_dates) & set(makeup_dates)
        if clash:
            raise ValueError(f"dates listed as both holiday and make-up day: {sorted(clash)}")
        return self


class HolidayCalendar(_Frozen):
    holidays: tuple[Holiday, ...]
    makeup_days: tuple[MakeupDay, ...]

    @property
    def holiday_dates(self) -> frozenset[date]:
        return frozenset(h.date for h in self.holidays)

    @property
    def makeup_dates(self) -> frozenset[date]:
        return frozenset(m.date for m in self.makeup_days)


def _data_file(country: str, year: int, data_dir: Path) -> Path:
    return data_dir / f"{country.lower()}_holidays_{year}.json"


def available_years(country: str = "VN", data_dir: Path = DATA_DIR) -> tuple[int, ...]:
    prefix = f"{country.lower()}_holidays_"
    return tuple(sorted(int(p.stem.removeprefix(prefix)) for p in data_dir.glob(f"{prefix}*.json")))


def load_holiday_year(year: int, country: str = "VN", data_dir: Path = DATA_DIR) -> HolidayYear:
    path = _data_file(country, year, data_dir)
    if not path.is_file():
        raise FileNotFoundError(f"no holiday data for {country} {year}: {path}")
    data = HolidayYear.model_validate_json(path.read_text(encoding="utf-8"))
    if data.year != year or data.country.upper() != country.upper():
        raise ValueError(f"{path.name} declares {data.country} {data.year}")
    return data


def load_holidays(
    years: Iterable[int] | None = None, country: str = "VN", data_dir: Path = DATA_DIR
) -> HolidayCalendar:
    """Merge the data files for ``years`` (all available years when ``None``)."""
    selected = available_years(country, data_dir) if years is None else sorted(set(years))
    loaded = [load_holiday_year(y, country, data_dir) for y in selected]
    return HolidayCalendar(
        holidays=tuple(h for year in loaded for h in year.holidays),
        makeup_days=tuple(m for year in loaded for m in year.makeup_days),
    )
