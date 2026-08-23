from fastapi.testclient import TestClient
from decimal import Decimal

from app.main import app
from app.controllers.sale_control import get_sale_service
from app.controllers.prod_control import get_product_service


class FakeProductService:
    def __init__(self):
        self._data = {}
        self._id = 1

    def add_product(self, product_data: dict):
        prod = product_data.copy()
        prod["id"] = self._id
        prod["price"] = Decimal(str(prod["price"]))
        self._data[self._id] = prod
        self._id += 1
        return prod

    def get_all_products(self):
        return list(self._data.values())

    def get_product(self, product_id: int):
        return self._data.get(product_id)

    def update_product(self, product_id: int, product_data: dict):
        if product_id not in self._data:
            return None
        prod = product_data.copy()
        prod["id"] = product_id
        prod["price"] = Decimal(str(prod["price"]))
        self._data[product_id] = prod
        return prod

    def delete_product(self, product_id: int):
        if product_id in self._data:
            del self._data[product_id]
            return True
        return False


class FakeSaleService:
    def __init__(self, product_service: FakeProductService):
        self._product_service = product_service
        self._sales = {}
        self._id = 1

    def create_sale(self, sale_data: dict):
        product = self._product_service.get_product(sale_data["product_id"])
        if product is None:
            raise ValueError("Product not found")
        if product["quantity"] < sale_data["quantity"]:
            raise ValueError("Insufficient stock")

        total_amount = Decimal(str(product["price"])) * sale_data["quantity"]
        product["quantity"] = product["quantity"] - sale_data["quantity"]

        sale = {
            "id": self._id,
            "product_id": sale_data["product_id"],
            "quantity": sale_data["quantity"],
            "total_amount": total_amount,
        }
        self._sales[self._id] = sale
        self._id += 1
        return sale

    def get_all_sales(self):
        return list(self._sales.values())

    def get_sale(self, sale_id: int):
        return self._sales.get(sale_id)


def setup_module():
    global fake_product_service, fake_sale_service
    fake_product_service = FakeProductService()
    fake_sale_service = FakeSaleService(fake_product_service)
    app.dependency_overrides[get_product_service] = lambda: fake_product_service
    app.dependency_overrides[get_sale_service] = lambda: fake_sale_service


client = TestClient(app)


def make_product_payload(quantity=5):
    return {
        "name": "Sale Product",
        "description": "For sale tests",
        "price": 20.0,
        "quantity": quantity,
        "category": "sale",
    }


def auth_headers(email: str, role: str):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Secret123@",
            "role": role,
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_sale_success():
    # create product
    supervisor = auth_headers("sale-supervisor@example.com", "supervisor")
    user = auth_headers("sale-user@example.com", "user")
    prod = client.post(
        "/products/", json=make_product_payload(10), headers=supervisor
    ).json()
    assert prod["id"] == 1

    sale_payload = {"product_id": 1, "quantity": 3}
    resp = client.post("/sales/", json=sale_payload, headers=user)
    assert resp.status_code == 200
    body = resp.json()
    assert body["product_id"] == 1
    assert body["quantity"] == 3


def test_create_sale_insufficient_stock():
    # product 1 now has 7 left from previous test
    user = auth_headers("sale-user-2@example.com", "user")
    resp = client.post(
        "/sales/", json={"product_id": 1, "quantity": 100}, headers=user
    )
    assert resp.status_code == 400


def test_create_sale_product_not_found():
    user = auth_headers("sale-user-3@example.com", "user")
    resp = client.post(
        "/sales/", json={"product_id": 9999, "quantity": 1}, headers=user
    )
    assert resp.status_code == 400


def test_get_all_sales():
    user = auth_headers("sale-user-4@example.com", "user")
    resp = client.get("/sales/", headers=user)
    assert resp.status_code == 200
    arr = resp.json()
    assert isinstance(arr, list)


def test_get_missing_sale_returns_404():
    user = auth_headers("sale-user-5@example.com", "user")
    resp = client.get("/sales/9999", headers=user)
    assert resp.status_code == 404
