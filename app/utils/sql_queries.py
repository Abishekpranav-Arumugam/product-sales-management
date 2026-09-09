# Products
INSERT_PRODUCT = """
            INSERT INTO products
            (name,description,price,quantity,
            category,created_at,updated_at)
            VALUES (:name,:description,:price,
            :quantity,:category,CURRENT_TIMESTAMP
            ,CURRENT_TIMESTAMP)
"""

SELECT_PRODUCT_BY_ID = """
                        SELECT id,name,description,price,quantity,
                        category FROM products WHERE id = :product_id
                        """


SELECT_ALL_PRODUCTS = """
                    SELECT id,name,description,price,quantity,
                    category FROM products ORDER BY id
                """


UPDATE_PRODUCT = """
UPDATE products
SET
    name = :name,
    description = :description,
    price = :price,
    quantity = :quantity,
    category = :category,
    updated_at = CURRENT_TIMESTAMP
    WHERE id = :product_id
"""

DELETE_PRODUCT = """
                DELETE FROM products WHERE id = :product_id
                """

# Sales

INSERT_SALE = """
                INSERT INTO sales (product_id,quantity,
                total_amount,created_at) VALUES (:product_id,
                :quantity,:total_amount,:created_at)
            """


SELECT_SALE_BY_ID = """
                    SELECT id,product_id,quantity,total_amount,
                      created_at FROM sales WHERE id = :sale_id
                    """


SELECT_ALL_SALES = """
                    SELECT id,product_id,quantity,total_amount,
                      created_at FROM sales ORDER BY id
                    """
