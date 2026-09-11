"""Database engine — Supabase PostgreSQL in production.

In the test environment, conftest.py injects DATABASE_URL=sqlite://...
before this module is imported. We detect that and allow SQLite for tests only,
so the full test suite can run without a live Supabase connection.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import ROOT, settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    # Read the URL directly from the environment so that test fixtures which
    # set os.environ['DATABASE_URL'] before importing this module are honoured,
    # even though settings() is cached and would otherwise return the default.
    url = os.environ.get('DATABASE_URL') or settings().database_url

    if not url and settings().app_env == 'development':
        url = f"sqlite:///{(ROOT / 'backend' / 'test.db').as_posix()}"

    if not url:
        raise RuntimeError(
            'DATABASE_URL is not set. '
            'Add DATABASE_URL=postgresql+psycopg://... to your .env file. '
            'See .env.example for the Supabase connection string format.'
        )

    if url.startswith('sqlite'):
        # Allowed only in the test environment (set by conftest.py).
        engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={'check_same_thread': False},
        )

        @event.listens_for(engine, 'connect')
        def _set_sqlite_pragma(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')

        return engine

    if not url.startswith('postgresql'):
        raise RuntimeError(
            f'DATABASE_URL must be a PostgreSQL connection string (got: {url!r}). '
            'Set DATABASE_URL=postgresql+psycopg://... in your .env file.'
        )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        # Supabase uses PgBouncer in transaction-pooling mode, which does not
        # support server-side prepared statements.  Disable psycopg's automatic
        # prepared-statement caching to avoid "prepared statement does not exist" errors.
        connect_args={'prepare_threshold': None},
    )


engine = _build_engine()
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
