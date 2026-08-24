import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DB_DRIVER", "sqlite")
os.environ.setdefault("DB_NAME", ":memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("PWD_ROUNDS", "100_000")

import pytest
from app.dal.database_manager import database_manager
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_db_state():
    if database_manager.engine.url.get_backend_name() == "sqlite":
        Base.metadata.drop_all(bind=database_manager.engine)
        Base.metadata.create_all(bind=database_manager.engine)
    yield
    if database_manager.engine.url.get_backend_name() == "sqlite":
        Base.metadata.drop_all(bind=database_manager.engine)
        Base.metadata.create_all(bind=database_manager.engine)
