import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# add project root for 'app' imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.db.session import Base  # noqa: E402
from app.core.config import settings  # noqa: E402
from app import models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer SYNC_DATABASE_URL; derive from async if necessary
db_url = os.getenv("SYNC_DATABASE_URL", getattr(settings, "SYNC_DATABASE_URL", None))
if not db_url:
    async_url = os.getenv("DATABASE_URL", getattr(settings, "DATABASE_URL", ""))
    db_url = async_url.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
