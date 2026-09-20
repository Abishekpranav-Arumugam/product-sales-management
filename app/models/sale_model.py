from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from app.models.base import Base


class Sale(Base):

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    product = relationship(
        "Product",
        back_populates="sales",
    )

    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )
