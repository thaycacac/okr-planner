import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import Engine, make_url, text

from tests.api_support import ApiHarness, migrate

TODAY = date(2026, 10, 1)

# Unset: every test gets its own SQLite file. Set (CI's Postgres job): tests share this database
# and each one starts from an empty ``public`` schema.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "").strip() or None


def _reset_postgres_schema(engine: Engine) -> None:
    database = engine.url.database or ""
    if "test" not in database:
        raise RuntimeError(
            f"TEST_DATABASE_URL points at {database!r}; tests drop its tables, so use a "
            "database whose name contains 'test'"
        )
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


@pytest.fixture
def empty_engine(tmp_path: Path) -> Iterator[Engine]:
    from app.persistence.db import create_db_engine

    if TEST_DATABASE_URL is None:
        engine = create_db_engine(f"sqlite:///{tmp_path / 'test.db'}")
    else:
        if make_url(TEST_DATABASE_URL).get_backend_name() != "postgresql":
            raise RuntimeError("TEST_DATABASE_URL must be a PostgreSQL URL")
        engine = create_db_engine(TEST_DATABASE_URL)
        _reset_postgres_schema(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_engine(empty_engine: Engine) -> Engine:
    migrate(empty_engine, "head")
    return empty_engine


@pytest.fixture
def api(db_engine: Engine) -> Iterator[ApiHarness]:
    with ApiHarness.start(db_engine, today=TODAY) as harness:
        yield harness
