import os

os.environ["APP_ENV"] = "test"
os.environ["DB_DRIVER"] = "sqlite"
os.environ["DB_NAME"] = ":memory:"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
os.environ["PWD_ROUNDS"] = "100_000"

import pytest  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.dal.database_manager import database_manager  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db_state():
    if database_manager.engine.url.get_backend_name() == "sqlite":
        Base.metadata.drop_all(bind=database_manager.engine)
        Base.metadata.create_all(bind=database_manager.engine)
    yield
    if database_manager.engine.url.get_backend_name() == "sqlite":
        Base.metadata.drop_all(bind=database_manager.engine)
        Base.metadata.create_all(bind=database_manager.engine)
