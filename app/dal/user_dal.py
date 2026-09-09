from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.user_model import User


class UserDAL:

    def __init__(self, db: Session) -> None:
        self.db = db

    def insert(self, user_data: dict[str, Any]) -> User:
        user = User(
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            role=user_data.get("role", "user"),
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self) -> list[User]:
        return self.db.query(User).order_by(User.id.asc()).all()

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user is None:
            return False
        self.db.delete(user)
        self.db.flush()
        return True
