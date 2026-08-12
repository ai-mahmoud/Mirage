"""Alembic environment: targets mirage_backend.database.Base's metadata,
and reads the database URL the same way the app does (BACKEND_DATABASE_URL
via mirage_backend.config), so migrations always run against whatever
database the running service would actually connect to."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from mirage_backend.config import load_config
from mirage_backend.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", load_config().database_url)


# ai/ and backend/ share one Postgres database ("mirage") but must not
# share Alembic's bookkeeping — a single "alembic_version" table would let
# the two services' independently-numbered revisions (both start at
# "0001") collide and desync each other's migration state. Each service
# tracks its own history in its own version table.
VERSION_TABLE = "alembic_version_backend"


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, version_table=VERSION_TABLE)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
