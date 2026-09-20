from typing import Any
from app.transaction.prod_interface import ProductInterface
from app.dal.product_dal import ProductDAL
from app.service.database_service import database_service
from app.utils.logger import get_logger
logger = get_logger(__name__)

class ProductService(ProductInterface):

    def add_product(self, product_data: dict[str, Any]) -> Any:
        db = database_service.create_session()
        try:
            product_dal = ProductDAL(db)
            product = product_dal.insert(product_data)
            db.commit()
            logger.info(
                "Product added successfully",
                extra={"product_id": product.id}
            )
            return product

        except Exception:
            db.rollback()
            logger.error(
                "Failed to add product due to database or validation error",
                extra={"error": str(e), "product_data": product_data}
            )
            raise

        finally:
            db.close()

    def get_all_products(self) -> list[Any]:
        db = database_service.create_session()
        try:
            product_dal = ProductDAL(db)
            return product_dal.get_all()
        finally:
            db.close()

    def get_product_by_id(self, product_id: int) -> Any:
        db = database_service.create_session()

        try:
            product_dal = ProductDAL(db)
            return product_dal.get_by_id(product_id)

        finally:
            db.close()

    def update_product(
        self, product_id: int, product_data: dict[str, Any]
    ) -> Any:
        db = database_service.create_session()

        try:
            product_dal = ProductDAL(db)
            product = product_dal.update(product_id, product_data)
            if product is not None:
                db.commit()
                logger.info(
                    "Product updated successfully",
                    extra={"product_id": product_id}
                )

            else:
                db.rollback()
                logger.warning(
                    "Attempted to update non-existent product",
                    extra={"product_id": product_id}
                )
            return product

        except Exception:
            db.rollback()
            logger.error(
                "Failed to update product due to system or database error",
                extra={"product_id": product_id, "error": str(e)}
            )
            raise

        finally:
            db.close()

    def delete_product(self, product_id: int) -> bool:
        db = database_service.create_session()

        try:
            product_dal = ProductDAL(db)
            deleted = product_dal.delete(product_id)

            if deleted:
                db.commit()
                logger.info(
                    "Product deleted successfully",
                    extra={"product_id": product_id}
                )
            else:
                db.rollback()
                logger.warning(
                    "Product deletion failed: Product not found",
                    extra={"product_id": product_id}
                )
            return deleted

        except Exception:
            db.rollback()
            logger.error(
                "Failed to delete product due to database error",
                extra={"product_id": product_id, "error": str(e)}
            )
            raise

        finally:
            db.close()

    def get_product(self, product_id: int) -> Any:
        return self.get_product_by_id(product_id)
