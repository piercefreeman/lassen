import os

from alembic import context
from sqlalchemy import engine, pool

from lassen.db.base_class import Base

# Your target_metadata
target_metadata = Base.metadata


def get_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ.get("POSTGRES_PASSWORD", "")
    server = os.environ.get("POSTGRES_SERVER", "localhost")
    db = os.environ["POSTGRES_DB"]
    return f"postgresql://{user}:{password}@{server}/{db}"


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = get_url()
    connectable = engine.create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()
