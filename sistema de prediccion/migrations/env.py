from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.settings import DATABASE_URL
from app.database.base import Base

# IMPORTANTE:
# Esto ejecuta app/models/__init__.py y registra
# todos los modelos ORM en Base.metadata.
import app.models


config = context.config


# Usar la DATABASE_URL proveniente del .env
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL
)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Metadata que Alembic utilizará para --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()