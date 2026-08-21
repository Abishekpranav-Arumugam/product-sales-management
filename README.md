# Test Suite Documentation

This project contains automated tests for the product and sales modules. The tests are organised into two main categories:

- Unit tests: validate the business logic and database layer in isolation.
- Integration/API tests: validate the FastAPI endpoints and request/response flow.

## Test hierarchy

Project
└── tests
    ├── test_product_dal.py
    │   └── test_product_dal_crud
    ├── test_product_service.py
    │   ├── test_product_service_add_and_get
    │   └── test_update_and_delete_product_branches
    ├── test_products.py
    │   ├── test_create_and_get_product
    │   ├── test_get_all_products_contains_created
    │   ├── test_update_product
    │   ├── test_delete_product
    │   └── test_get_missing_product_returns_404
    ├── test_sale_dal.py
    │   └── test_sale_dal_insert_and_get
    ├── test_sale_service.py
    │   └── test_sale_service_create_and_errors
    └── test_sales.py
        ├── test_create_sale_success
        ├── test_create_sale_insufficient_stock
        ├── test_create_sale_product_not_found
        ├── test_get_all_sales
        └── test_get_missing_sale_returns_404

---

## 1. Product DAL tests

File: [tests/test_product_dal.py](tests/test_product_dal.py)

### Test: test_product_dal_crud

This is a unit test for the product data access layer.

It checks the full CRUD flow for a product:

- creates an in-memory SQLite database
- inserts a product record
- fetches the product by ID
- retrieves all products
- updates the product details
- updates the product quantity
- deletes the product
- confirms the product no longer exists

This confirms that the database logic in the ProductDAL class works correctly.

---

## 2. Product service tests

File: [tests/test_product_service.py](tests/test_product_service.py)

### Test: test_product_service_add_and_get

This is a unit test for the product service layer.

It verifies that the service can:

- add a new product
- fetch all products
- fetch a product by ID

It ensures the service layer works correctly when it interacts with the database session.

### Test: test_update_and_delete_product_branches

This test validates the edge cases of the product service logic:

- updating a product that does not exist returns None
- creating a product and then deleting it works successfully
- deleting a product that does not exist returns False

This ensures the service handles both valid and invalid operations safely.

---

## 3. Product API integration tests

File: [tests/test_products.py](tests/test_products.py)

These tests validate the REST API for products using FastAPI TestClient.

### Test: test_create_and_get_product

Checks that the API can:

- create a product using POST /products/
- read the created product using GET /products/{id}

This verifies that product creation and retrieval are working from the API layer.

### Test: test_get_all_products_contains_created

Checks that the API returns all products and that the newly created product appears in the list.

### Test: test_update_product

Checks that a product can be updated through the PUT /products/{id} endpoint.

### Test: test_delete_product

Checks that a product can be deleted through the DELETE /products/{id} endpoint.

### Test: test_get_missing_product_returns_404

Checks the API returns 404 when a product ID does not exist.

This validates error handling for missing records.

---

## 4. Sale DAL tests

File: [tests/test_sale_dal.py](tests/test_sale_dal.py)

### Test: test_sale_dal_insert_and_get

This is a unit test for the sale data access layer.

It verifies that the system can:

- create a product record
- insert a sale record linked to that product
- fetch all sales
- fetch a sale by ID

This validates the sale table and its relationship to the products table.

---

## 5. Sale service tests

File: [tests/test_sale_service.py](tests/test_sale_service.py)

### Test: test_sale_service_create_and_errors

This is a service-layer unit test for sale logic.

It checks the business rules for creating a sale:

- a valid sale succeeds
- sale creation fails when stock is insufficient
- sale creation fails when the product does not exist

This confirms that the service enforces the core business rules for sales.

---

## 6. Sale API integration tests

File: [tests/test_sales.py](tests/test_sales.py)

These tests validate the REST API for sales using FastAPI TestClient.

### Test: test_create_sale_success

Checks that a sale can be created successfully through the POST /sales/ endpoint.

### Test: test_create_sale_insufficient_stock

Checks that the API returns 400 when the requested quantity is more than available stock.

### Test: test_create_sale_product_not_found

Checks that the API returns 400 when the product ID does not exist.

### Test: test_get_all_sales

Checks that the API returns the full list of sales records.

### Test: test_get_missing_sale_returns_404

Checks that the API returns 404 when a sale ID does not exist.

---

## Overall testing approach

This project uses both of the following testing approaches:

### Unit testing

Used for:

- database logic in the DAL layer
- business rules in the service layer

These tests are fast and verify the core logic without depending on HTTP requests.

### Integration testing

Used for:

- API endpoints in the controller layer
- request and response handling through FastAPI

These tests confirm the system works from the outside, as a real client would use it.

---

## Test execution order

When pytest runs, it discovers tests based on file names and function names. In this project, the execution order is:

1. test_product_dal.py
2. test_product_service.py
3. test_products.py
4. test_sale_dal.py
5. test_sale_service.py
6. test_sales.py

Within each file, the tests run in the order they are defined.

This test suite provides good coverage for both the product and sales modules and validates the application at multiple layers.
