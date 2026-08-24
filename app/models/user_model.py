from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(
        String(20), default="user", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False)
