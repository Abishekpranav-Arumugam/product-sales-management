from typing import Any
import csv
import io
from app.transaction.sale_interface import SaleInterface
from app.dal.sale_dal import SaleDAL
from app.dal.product_dal import ProductDAL
from app.service.database_service import database_service
from app.utils.logger import get_logger
logger = get_logger(__name__)

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
                logger.error(
                    "Sale failed: Product not found",
                    extra={"product_id": product_id}
                )
                raise ValueError("Product not found")

            if product.quantity < quantity:
                logger.warning(
                    "Sale failed: Insufficient stock available",
                    extra={
                        "product_id": product_id,
                        "available_quantity": product.quantity,
                        "requested_quantity": quantity
                    }
                )
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
            logger.info(
                "Sale transaction successfully logged",
                extra={
                    "sale_id": sale.id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "total_amount": float(total_amount)
                }
            )

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

    def generate_sales_report(self) -> str:
        """
        Fetches all sales records and formats them as a CSV-compliant string.
        """
        db = database_service.create_session()
        try:
            sale_dal = SaleDAL(db)
            sales = sale_dal.get_all()

            # Create an in-memory string stream
            output = io.StringIO()
            writer = csv.writer(output)

            # Write CSV Headers
            writer.writerow(["ID", "Product ID", "Quantity",
                            "Total Amount", "Created At"])

            # Write DB data rows
            for sale in sales:
                writer.writerow([
                    sale.id,
                    sale.product_id,
                    sale.quantity,
                    float(sale.total_amount),
                    sale.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S") if sale.created_at else ""
                ])

            return output.getvalue()
        finally:
            db.close()
