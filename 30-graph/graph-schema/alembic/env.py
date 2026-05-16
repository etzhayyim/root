from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from alembic.runtime.migration import HeadMaintainer
from sqlalchemy import event
from sqlalchemy import literal_column

from graph_schema.db import _rewrite_risingwave_statement, database_url, make_engine


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None
VERSION_TABLE = "graph_schema_alembic_live"


def _risingwave_update_version(self: HeadMaintainer, from_: str, to_: str) -> None:
    assert to_ not in self.heads
    self.heads.remove(from_)
    self.heads.add(to_)

    self.context.impl._exec(
        self.context._version.delete().where(
            self.context._version.c.version_num == literal_column("'%s'" % from_)
        )
    )
    self.context.impl._exec(
        self.context._version.insert().values(
            version_num=literal_column("'%s'" % to_)
        )
    )


HeadMaintainer._update_version = _risingwave_update_version


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        transactional_ddl=False,
        version_table=VERSION_TABLE,
        version_table_pk=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = make_engine()
    with engine.connect() as connection:
        event.listen(
            connection,
            "before_cursor_execute",
            lambda conn, cursor, statement, parameters, context, executemany: (
                _rewrite_risingwave_statement(statement),
                parameters,
            ),
            retval=True,
        )
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transactional_ddl=False,
            version_table=VERSION_TABLE,
            version_table_pk=False,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
