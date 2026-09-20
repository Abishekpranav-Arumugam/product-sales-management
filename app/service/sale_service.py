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

    def process_sale_queue(
        self, sale_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Encapsulates the transactional stock validation and reduction logic
        on the Database side for the producer queue.
        """
        db = database_service.create_session()
        try:
            product_dal = ProductDAL(db)
            product_id = sale_data["product_id"]
            quantity = sale_data["quantity"]

            # 1. Fetch product from database
            product = product_dal.get_by_id(product_id)
            if product is None:
                raise ValueError("Product not found")

            # 2. Check stock availability
            if product.quantity < quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {product.quantity}"
                )

            # 3. Deduct stock and commit changes to DB in real-time
            new_quantity = product.quantity - quantity
            product_dal.update_quantity(product_id, new_quantity)
            db.commit()

            # === Code updated here (Calculated and included total_amount) ===
            total_amount = float(product.price * quantity)

            return {
                "product_id": product_id,
                "quantity": quantity,
                "remaining_quantity": new_quantity,
                "total_amount": total_amount,
                "selling_price": float(product.price),
            }
            # ===============================================================

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # === Code updated here (Simplified to only write the sales invoice) ===
    def create_sale(self, sale_data: dict[str, Any]) -> Any:
        """
        Asynchronously called by the consumer daemon to write the final
        sales invoice to PostgreSQL.
        """
        db = database_service.create_session()
        try:
            sale_dal = SaleDAL(db)
            product_id = sale_data["product_id"]
            quantity = sale_data["quantity"]
            total_amount = sale_data.get("total_amount")
            selling_price = sale_data.get("selling_price")

            if total_amount is None or selling_price is None:
                product_dal = ProductDAL(db)
                product = product_dal.get_by_id(product_id)
                if product is None:
                    raise ValueError("Product not found")
                if total_amount is None and product.quantity < quantity:
                    raise ValueError(
                        f"Insufficient stock. Available: {product.quantity}"
                    )
                if total_amount is None:
                    total_amount = float(product.price * quantity)
                if selling_price is None:
                    selling_price = float(product.price)

            # Since the stock has already been reserved, the consumer
            # only needs to write the final receipt invoice.
            sale = sale_dal.insert({
                "product_id": product_id,
                "quantity": quantity,
                "total_amount": total_amount,
                "selling_price": selling_price,
            })
            db.commit()

            logger.info(
                "Asynchronously saved sale invoice to database",
                extra={"sale_id": sale.id}
            )
            return sale

        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to write sale invoice asynchronously",
                extra={"error": str(e), "sale_data": sale_data}
            )
            raise
        finally:
            db.close()
    # ======================================================================

    def get_all_sales(self) -> list[Any]:
        db = database_service.create_session()
        try:
            sale_dal = SaleDAL(db)
            return sale_dal.get_all()

        finally:
            db.close()

    def get_sales_page(
        self, page: int, page_size: int
    ) -> tuple[list[Any], int]:
        db = database_service.create_session()
        try:
            sale_dal = SaleDAL(db)
            return sale_dal.get_page(page, page_size)
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
