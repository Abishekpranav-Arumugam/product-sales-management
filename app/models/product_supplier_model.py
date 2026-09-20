from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    product = relationship(
        "Product",
        back_populates="product_suppliers"
    )

    supplier = relationship(
        "Supplier",
        back_populates="product_suppliers"
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "supplier_id",
            name="uq_product_supplier"
        ),
    )
