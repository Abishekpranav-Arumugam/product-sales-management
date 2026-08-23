import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.product_model import Product
from app.models.sale_model import Sale
from app.models.user_model import User


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(
    dotenv_path=BASE_DIR / ".env",
    override=False,
)


class DatabaseManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating DatabaseManager Singleton Instance")
            cls._instance = super().__new__(cls)
            cls._instance.initialize_database()
        return cls._instance

    def initialize_database(self):

        app_env = os.getenv("APP_ENV")
        driver = os.getenv("DB_DRIVER")
        db_user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")

        required_variables = {
            "APP_ENV": app_env,
            "DB_DRIVER": driver,
            "DB_USER": db_user,
            "DB_PASSWORD": password,
            "DB_HOST": host,
            "DB_PORT": port,
            "DB_NAME": database,
        }

        missing_variables = [
            name
            for name, value in required_variables.items()
            if not value
        ]

        if missing_variables:
            raise RuntimeError(
                f"Missing environment variables: {
                    ', '.join(missing_variables)}"
            )

        if app_env and app_env.lower() == "test":
            # Use a shared in-memory SQLite database during tests so that
            # the metadata.create_all() call and test-session connections
            # see the same database. StaticPool + check_same_thread=False
            # keeps a single connection that all sessions reuse.
            database_url = "sqlite:///:memory:"

            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False,
            )

        else:
            database_url = URL.create(
                drivername=driver,
                username=db_user,
                password=password,
                host=host,
                port=int(port),
                database=database,
            )

            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                echo=False,
            )

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

        Base.metadata.create_all(bind=self.engine)
        self._ensure_user_role_column()

    def _ensure_user_role_column(self):
        user_columns = {
            column["name"] for column in inspect(self.engine).get_columns("users")
        }
        if "role" in user_columns:
            return

        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                )
            )


database_manager = DatabaseManager()
