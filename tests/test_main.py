import pytest

# `fastapi.testclient` (Starlette TestClient) depends on `httpx`.
# If `httpx` isn't installed yet, skip tests instead of failing collection.
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

import app.main as main


app = main.app


client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello from FastAPI"}


def test_echo() -> None:
    resp = client.post("/echo", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"message": "hi"}


class FakeCustomerResource:
    def get(self, template):
        assert template == {"country": "USA"}
        return {"items": [{"customerNumber": 103, "customerName": "Atelier", "contactLastName": "Schmitt", "contactFirstName": "Carine", "phone": "40.32.2555", "addressLine1": "54, rue Royale", "addressLine2": None, "city": "Nantes", "state": None, "postalCode": "44000", "country": "USA", "salesRepEmployeeNumber": 1370, "creditLimit": "21000.00"}]}

    def get_by_id(self, id):
        if str(id) == "103":
            return {"customerNumber": 103, "customerName": "Atelier", "contactLastName": "Schmitt", "contactFirstName": "Carine", "phone": "40.32.2555", "addressLine1": "54, rue Royale", "addressLine2": None, "city": "Nantes", "state": None, "postalCode": "44000", "country": "France", "salesRepEmployeeNumber": 1370, "creditLimit": "21000.00"}
        raise ValueError("No customer with id '999'")

    def post(self, new_data):
        assert new_data.customerName == "New Corp"
        return "104"

    def put(self, customer_id, new_data):
        if str(customer_id) == "999":
            return 0
        return 1

    def delete(self, customer_id):
        return 1 if str(customer_id) == "103" else 0


class FakeOrderResource:
    def get(self, template):
        assert template == {"status": "Shipped"}
        return {"items": [{"orderNumber": 10100, "orderDate": "2003-01-06", "requiredDate": "2003-01-13", "shippedDate": "2003-01-10", "status": "Shipped", "comments": None, "customerNumber": 103}]}

    def get_by_id(self, id):
        if str(id) == "10100":
            return {"orderNumber": 10100, "orderDate": "2003-01-06", "requiredDate": "2003-01-13", "shippedDate": "2003-01-10", "status": "Shipped", "comments": None, "customerNumber": 103}
        raise ValueError(f"No order with id {id!r}")

    def post(self, new_data):
        return "10101"

    def put(self, order_id, new_data):
        return 1 if str(order_id) == "10100" else 0

    def delete(self, order_id):
        return 1 if str(order_id) == "10100" else 0


class FakeOrderDetailsResource:
    def get(self, template):
        if template == {"orderNumber": "10100"}:
            return {"items": [{"orderNumber": 10100, "productCode": "S18_1749", "quantityOrdered": 30, "priceEach": "136.00", "orderLineNumber": 3}]}
        assert template == {"productCode": "S18_1749"}
        return {"items": [{"orderNumber": 10100, "productCode": "S18_1749", "quantityOrdered": 30, "priceEach": "136.00", "orderLineNumber": 3}]}

    def get_by_id(self, key):
        if key == {"orderNumber": 10100, "productCode": "S18_1749"}:
            return {"orderNumber": 10100, "productCode": "S18_1749", "quantityOrdered": 30, "priceEach": "136.00", "orderLineNumber": 3}
        raise ValueError("No order detail with key (999, 'BAD')")

    def post(self, new_data):
        return '{"orderNumber": 10100, "productCode": "S18_1749"}'

    def put(self, key, new_data):
        return 1 if key == {"orderNumber": 10100, "productCode": "S18_1749"} else 0

    def delete(self, key):
        return 1 if key == {"orderNumber": 10100, "productCode": "S18_1749"} else 0


@pytest.fixture(autouse=True)
def patch_resources(monkeypatch):
    monkeypatch.setattr(main, "customer_resource", FakeCustomerResource())
    monkeypatch.setattr(main, "order_resource", FakeOrderResource())
    monkeypatch.setattr(main, "order_details_resource", FakeOrderDetailsResource())


def test_get_customers() -> None:
    resp = client.get("/customers?country=USA")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["customerNumber"] == 103


def test_create_customer() -> None:
    payload = {
        "customerName": "New Corp",
        "contactLastName": "Doe",
        "contactFirstName": "Jane",
        "phone": "555-0100",
        "addressLine1": "1 Main St",
        "city": "New York",
        "country": "USA",
    }
    resp = client.post("/customers", json=payload)
    assert resp.status_code == 200
    assert resp.json() == "104"


def test_get_customer_not_found() -> None:
    resp = client.get("/customers/999")
    assert resp.status_code == 404


def test_delete_customer_not_found() -> None:
    resp = client.delete("/customers/999")
    assert resp.status_code == 404


def test_get_orders() -> None:
    resp = client.get("/orders?status=Shipped")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["orderNumber"] == 10100


def test_update_order() -> None:
    payload = {
        "orderDate": "2003-01-06",
        "requiredDate": "2003-01-13",
        "shippedDate": "2003-01-10",
        "status": "Shipped",
        "comments": "updated",
        "customerNumber": 103,
    }
    resp = client.put("/orders/10100", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"updated": 1}


def test_get_order_details_collection() -> None:
    resp = client.get("/orderdetails?productCode=S18_1749")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["productCode"] == "S18_1749"


def test_get_order_details_by_order() -> None:
    resp = client.get("/orders/10100/orderdetails")
    assert resp.status_code == 200
    assert resp.json()["items"][0]["orderNumber"] == 10100


def test_get_order_detail_by_id() -> None:
    resp = client.get("/orders/10100/orderdetails/S18_1749")
    assert resp.status_code == 200
    assert resp.json()["productCode"] == "S18_1749"


def test_delete_order_detail_not_found() -> None:
    resp = client.delete("/orders/999/orderdetails/BAD")
    assert resp.status_code == 404
