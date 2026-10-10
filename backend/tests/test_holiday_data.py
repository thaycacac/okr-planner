import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.calendar import available_years, load_holiday_year, load_holidays


def test_ships_vn_data_for_2026_and_2027() -> None:
    assert {2026, 2027} <= set(available_years())


@pytest.mark.parametrize("year", [2026, 2027])
def test_every_year_cites_sources(year: int) -> None:
    data = load_holiday_year(year)
    assert data.sources
    assert all(s.url.startswith("https://") for s in data.sources)


@pytest.mark.parametrize(
    ("day", "name_fragment"),
    [
        (date(2026, 1, 1), "Tết Dương lịch"),
        (date(2026, 2, 17), "mùng 1"),
        (date(2026, 4, 26), "Giỗ Tổ"),
        (date(2026, 4, 27), "Nghỉ bù"),
        (date(2026, 4, 30), "Chiến thắng"),
        (date(2026, 5, 1), "Lao động"),
        (date(2026, 9, 1), "Quốc khánh"),
        (date(2026, 9, 2), "Quốc khánh"),
        (date(2027, 1, 1), "Tết Dương lịch"),
        (date(2027, 2, 6), "mùng 1"),
        (date(2027, 4, 16), "Giỗ Tổ"),
        (date(2027, 4, 30), "Chiến thắng"),
        (date(2027, 5, 3), "Nghỉ bù"),
        (date(2027, 9, 2), "Quốc khánh"),
    ],
)
def test_contains_key_vn_holidays(day: date, name_fragment: str) -> None:
    by_date = {h.date: h for h in load_holidays().holidays}
    assert name_fragment in by_date[day].name_vi


def test_tet_2026_covers_official_five_days() -> None:
    holidays = load_holidays([2026]).holiday_dates
    assert {date(2026, 2, d) for d in range(16, 21)} <= holidays


def test_2026_official_makeup_saturday() -> None:
    assert load_holidays([2026]).makeup_dates == frozenset({date(2026, 8, 22)})


def test_unconfirmed_2027_entries_are_marked_provisional() -> None:
    by_date = {h.date: h for h in load_holiday_year(2027).holidays}
    assert by_date[date(2027, 2, 6)].status == "provisional"
    assert by_date[date(2027, 9, 3)].status == "provisional"
    assert by_date[date(2027, 9, 2)].status == "official"


def test_missing_year_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_holiday_year(1999)


def _write(tmp_path: Path, payload: dict[str, object]) -> Path:
    base = json.loads(load_holiday_year(2026).model_dump_json())
    base.update(payload)
    (tmp_path / "vn_holidays_2026.json").write_text(json.dumps(base), encoding="utf-8")
    return tmp_path


def test_edited_data_file_is_picked_up(tmp_path: Path) -> None:
    holiday = {
        "date": "2026-12-31",
        "name_vi": "Nghỉ công ty",
        "name_en": "Company day off",
        "kind": "public_holiday",
        "status": "official",
        "source": "blld-2019",
    }
    data_dir = _write(tmp_path, {"holidays": [holiday]})
    assert load_holidays(data_dir=data_dir).holiday_dates == frozenset({date(2026, 12, 31)})


@pytest.mark.parametrize(
    "bad_holiday",
    [
        {"date": "2027-01-01"},
        {"source": "unknown"},
        {"kind": "birthday"},
    ],
)
def test_rejects_inconsistent_entries(tmp_path: Path, bad_holiday: dict[str, str]) -> None:
    holiday = {
        "date": "2026-12-31",
        "name_vi": "x",
        "name_en": "x",
        "kind": "public_holiday",
        "status": "official",
        "source": "blld-2019",
        **bad_holiday,
    }
    data_dir = _write(tmp_path, {"holidays": [holiday]})
    with pytest.raises(ValidationError):
        load_holiday_year(2026, data_dir=data_dir)


def test_rejects_date_listed_as_holiday_and_makeup(tmp_path: Path) -> None:
    makeup = {
        "date": "2026-01-01",
        "reason_vi": "x",
        "reason_en": "x",
        "status": "official",
        "source": "blld-2019",
    }
    data_dir = _write(tmp_path, {"makeup_days": [makeup]})
    with pytest.raises(ValidationError):
        load_holiday_year(2026, data_dir=data_dir)
