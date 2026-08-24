from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.product_model import Product


class ProductDAL:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ========================================================
    # INSERT PRODUCT
    # ========================================================

    def insert(self, product_data: dict[str, Any]) -> Product:

        product = Product(
            name=product_data["name"],
            description=product_data.get("description"),
            price=product_data["price"],
            quantity=product_data["quantity"],
            category=product_data["category"],
        )

        self.db.add(product)

        self.db.flush()

        self.db.refresh(product)

        return product

    # ========================================================
    # GET ALL PRODUCTS
    # ========================================================

    def get_all(self) -> list[Product]:

        products = self.db.query(Product).order_by(Product.id.desc()).all()

        return products

    # ========================================================
    # GET PRODUCT BY ID
    # ========================================================

    def get_by_id(self, product_id: int) -> Optional[Product]:

        product = self.db.query(Product).filter(
            Product.id == product_id).first()

        return product

    # ========================================================
    # UPDATE PRODUCT
    # ========================================================

    def update(
        self, product_id: int, product_data: dict[str, Any]
    ) -> Optional[Product]:

        product = self.get_by_id(product_id)

        if product is None:
            return None

        product.name = product_data["name"]
        product.description = product_data.get("description")
        product.price = product_data["price"]
        product.quantity = product_data["quantity"]
        product.category = product_data["category"]

        self.db.flush()

        self.db.refresh(product)

        return product

    # ========================================================
    # UPDATE PRODUCT QUANTITY
    # ========================================================

    def update_quantity(
        self, product_id: int, quantity: int
    ) -> Optional[Product]:

        product = self.get_by_id(product_id)

        if product is None:
            return None

        product.quantity = quantity

        self.db.flush()

        self.db.refresh(product)

        return product

    # ========================================================
    # DELETE PRODUCT
    # ========================================================

    def delete(self, product_id: int) -> bool:

        product = self.get_by_id(product_id)

        if product is None:
            return False

        self.db.delete(product)

        self.db.flush()

        return True
