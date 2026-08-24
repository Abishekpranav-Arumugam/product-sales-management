from datetime import datetime

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.sale_model import Sale


class SaleDAL:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ========================================================
    # INSERT SALE
    # ========================================================

    def insert(self, sale_data: dict[str, Any]) -> Sale:

        sale = Sale(
            product_id=sale_data["product_id"],
            quantity=sale_data["quantity"],
            total_amount=sale_data["total_amount"],
            created_at=datetime.now(),
        )

        self.db.add(sale)

        self.db.flush()

        self.db.refresh(sale)

        return sale

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
