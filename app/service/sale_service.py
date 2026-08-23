from typing import Any

from app.transaction.sale_interface import SaleInterface
from app.dal.sale_dal import SaleDAL
from app.dal.product_dal import ProductDAL
from app.service.database_service import database_service


class SaleService(SaleInterface):

    def create_sale(self, sale_data: dict[str, Any]) -> Any:

        db = database_service.create_session()

        try:

            product_dal = ProductDAL(db)
            sale_dal = SaleDAL(db)

            product_id = sale_data["product_id"]
            quantity = sale_data["quantity"]

            product = product_dal.get_by_id(product_id)

            if product is None:

                raise ValueError("Product not found")

            if product.quantity < quantity:

                raise ValueError("Insufficient stock")

            total_amount = product.price * quantity

            updated_quantity = product.quantity - quantity

            product_dal.update_quantity(product_id, updated_quantity)

            sale_record = {
                "product_id": product_id,
                "quantity": quantity,
                "total_amount": total_amount,
            }

            sale = sale_dal.insert(sale_record)

            db.commit()

            return sale

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    def get_all_sales(self) -> list[Any]:

        db = database_service.create_session()

        try:

            sale_dal = SaleDAL(db)

            return sale_dal.get_all()

        finally:

            db.close()

    def get_sale_by_id(self, sale_id: int) -> Any:

        db = database_service.create_session()

        try:

            sale_dal = SaleDAL(db)

            return sale_dal.get_by_id(sale_id)

        finally:

            db.close()

    def get_sale(self, sale_id: int) -> Any:

        return self.get_sale_by_id(sale_id)
