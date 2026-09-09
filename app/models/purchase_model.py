from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False
    )

    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    purchased_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    product = relationship(
        "Product",
        back_populates="purchases"
    )

    supplier = relationship(
        "Supplier",
        back_populates="purchases"
    )
