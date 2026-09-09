from datetime import datetime
import os
from zoneinfo import ZoneInfo

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.product_model import Product
from app.models.sale_model import Sale


class SaleDAL:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ========================================================
    # INSERT SALE
    # ========================================================

    def insert(self, sale_data: dict[str, Any]) -> Sale:
        product = self.db.get(Product, sale_data["product_id"])
        if product is None:
            raise ValueError("Product not found")

        selling_price = sale_data.get("selling_price")
        if selling_price is None:
            selling_price = float(product.price)

        total_amount = sale_data.get("total_amount")
        if total_amount is None:
            total_amount = selling_price * sale_data["quantity"]

        sale = Sale(
            product_id=sale_data["product_id"],
            quantity=sale_data["quantity"],
            total_amount=total_amount,
            selling_price=selling_price,
            created_at=self._current_app_time(),
        )

        self.db.add(sale)

        self.db.flush()

        self.db.refresh(sale)

        return sale

    def _current_app_time(self) -> datetime:
        timezone_name = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
        return datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)

    # ========================================================
    # GET ALL SALES
    # ========================================================

    def get_all(self) -> list[Sale]:

        sales = self.db.query(Sale).order_by(Sale.id.desc()).all()

        return sales

    # ========================================================
    # GET SALE BY ID
    # ========================================================

    def get_by_id(self, sale_id: int) -> Optional[Sale]:

        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()

        return sale
