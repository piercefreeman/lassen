from json import dumps as json_dumps
from os import environ

import pytest

from lassen.core.config import CoreSettings, register_settings
from lassen.db.session import get_db_context


@pytest.fixture(autouse=True, scope="session")
def inject_env_variables():
    """
    Inject fake environment variables for testing purposes.

    """
    settings = CoreSettings(
        BACKEND_CORS_ORIGINS=["http://localhost"],
        SERVER_NAME="lassen-test",
        SERVER_HOST="http://localhost",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="lassen",
        POSTGRES_PASSWORD="mypassword",
        POSTGRES_DB="lassen_test_db",
    )

    # Convert settings into env variables
    for key, value in settings.dict().items():
        if value:
            if isinstance(value, list):
                value = json_dumps(value)
            else:
                value = str(value)

            print(f"Test Env: Will set `{key}` = `{value}`")
            environ[key] = value

    # We don't have a client-specific settings object, so we'll just back-register the core settings
    register_settings(CoreSettings)


@pytest.fixture()
def db_session():
    with get_db_context() as db:
        # Make sure each test has a fresh context
        from lassen.db.base_class import Base

        Base.metadata.drop_all(bind=db.bind)
        Base.metadata.create_all(bind=db.bind)

        yield db
