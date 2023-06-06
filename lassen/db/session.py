from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lassen.core.config import get_settings

SessionLocal = None


def get_session_local():
    global SessionLocal

    settings = get_settings()
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


@contextmanager
def get_db_context():
    db = None
    try:
        db = get_session_local()()
        yield db
    finally:
        if db is not None:
            db.close()
