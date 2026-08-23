from typing import Any
from app.transaction.prod_interface import ProductInterface
from app.dal.product_dal import ProductDAL
from app.service.database_service import database_service


class ProductService(ProductInterface):

    def add_product(self, product_data: dict[str, Any]) -> Any:

        db = database_service.create_session()
        try:
            product_dal = ProductDAL(db)
            product = product_dal.insert(product_data)
            db.commit()
            return product

        except Exception:
            db.rollback()
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

    def update_product(self, product_id: int, product_data: dict[str, Any]) -> Any:

        db = database_service.create_session()

        try:

            product_dal = ProductDAL(db)

            product = product_dal.update(product_id, product_data)

            if product is not None:
                db.commit()
            else:
                db.rollback()

            return product

        except Exception:

            db.rollback()

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
            else:
                db.rollback()

            return deleted

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    def get_product(self, product_id: int) -> Any:

        return self.get_product_by_id(product_id)
