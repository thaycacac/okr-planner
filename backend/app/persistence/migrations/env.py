from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

from app.persistence import models  # noqa: F401  (registers tables on Base.metadata)
from app.persistence.db import Base, get_engine

config = context.config
# Programmatic callers (tests) pass their own connection and keep their logging setup.
external_connection: Connection | None = config.attributes.get("connection")
if config.config_file_name is not None and external_connection is None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(get_engine().url),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    if external_connection is not None:
        _run(external_connection)
        return
    with get_engine().connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
