from fastapi.testclient import TestClient
from decimal import Decimal

from app.main import app
from app.controllers.prod_control import get_product_service


class FakeProductService:
    def __init__(self):
        self._data = {}
        self._id = 1

    def add_product(self, product_data: dict):
        prod = product_data.copy()
        prod["id"] = self._id
        # ensure Decimal for price
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


def setup_module() -> None:
    # install dependency override once per module
    global fake_service
    fake_service = FakeProductService()
    app.dependency_overrides[get_product_service] = lambda: fake_service


client = TestClient(app)


def make_product_payload():
    return {
        "name": "Test Product",
        "description": "A product for tests",
        "price": 9.99,
        "quantity": 10,
        "category": "test",
    }


def supervisor_headers():
    response = client.post(
        "/auth/register",
        json={
            "email": "product-supervisor@example.com",
            "password": "Secret123@",
            "role": "supervisor",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_and_get_product() -> None:
    headers = supervisor_headers()
    resp = client.post(
        "/products/", json=make_product_payload(), headers=headers)
    assert resp.status_code == 200
    created = resp.json()
    assert created["id"] == 1
    assert created["name"] == "Test Product"

    get_resp = client.get("/products/1", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == 1


def test_get_all_products_contains_created() -> None:
    resp = client.get("/products/", headers=supervisor_headers())
    assert resp.status_code == 200
    arr = resp.json()
    assert isinstance(arr, list)
    assert any(p["id"] == 1 for p in arr)


def test_update_product() -> None:
    payload = make_product_payload()
    payload["name"] = "Updated"
    resp = client.put("/products/1", json=payload,
                      headers=supervisor_headers())
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


def test_delete_product() -> None:
    resp = client.delete("/products/1", headers=supervisor_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["product_id"] == 1


def test_get_missing_product_returns_404() -> None:
    resp = client.get("/products/9999", headers=supervisor_headers())
    assert resp.status_code == 404
