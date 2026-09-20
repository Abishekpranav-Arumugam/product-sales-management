from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    contact: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    product_suppliers = relationship(
        "ProductSupplier",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )

    purchases = relationship(
        "Purchase",
        back_populates="supplier"
    )
