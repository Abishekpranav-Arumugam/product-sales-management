from sqlalchemy.orm import Session

from app.dal.database_manager import database_manager


class DatabaseService:
    def create_session(self) -> Session:
        return database_manager.SessionLocal()


database_service = DatabaseService()


def get_db() -> Session:
    db = database_manager.SessionLocal()
    try:
        yield db
    finally:
        db.close()
