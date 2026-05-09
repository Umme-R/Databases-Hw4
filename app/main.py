from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi import Request
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

if __package__ in (None, ""):
    # Supports running this file directly (e.g., PyCharm "main.py" debug config).
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.resources.HarryPotterResource import (
        HarryPotterCharacter,
        HarryPotterCollection,
        HarryPotterResource,
    )
    from app.resources.CustomerResource import Customer, CustomerCollection, CustomerResource
    from app.resources.OrderResource import Order, OrderCollection, OrderResource
    from app.resources.OrderDetailsResource import (
        OrderDetail,
        OrderDetailsCollection,
        OrderDetailsResource,
    )
else:
    from .resources.HarryPotterResource import (
        HarryPotterCharacter,
        HarryPotterCollection,
        HarryPotterResource,
    )
    from .resources.CustomerResource import Customer, CustomerCollection, CustomerResource
    from .resources.OrderResource import Order, OrderCollection, OrderResource
    from .resources.OrderDetailsResource import (
        OrderDetail,
        OrderDetailsCollection,
        OrderDetailsResource,
    )


def _get_app_name() -> str:
    # Keep settings minimal in this starter; use environment variables when needed.
    return os.getenv("APP_NAME", "Starter FastAPI App")


app = FastAPI(title=_get_app_name(), version="0.1.0")
harry_potter_resource = HarryPotterResource()
customer_resource = CustomerResource()
order_resource = OrderResource()
order_details_resource = OrderDetailsResource()


class EchoRequest(BaseModel):
    message: str


def _query_template(request: Request) -> dict[str, str]:
    return {key: value for key, value in request.query_params.items() if value != ""}


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo", tags=["echo"])
def echo(payload: EchoRequest) -> EchoRequest:
    return payload


@app.get("/harry-potter", tags=["harry-potter"])
def get_harry_potter_characters(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    house_name: Optional[str] = None,
) -> HarryPotterCollection:
    template: dict = {}
    if first_name is not None:
        template["first_name"] = first_name
    if last_name is not None:
        template["last_name"] = last_name
    if house_name is not None:
        template["house_name"] = house_name
    return harry_potter_resource.get(template)


@app.get("/harry-potter/{character_id}", tags=["harry-potter"])
def get_harry_potter_character_by_id(character_id: str) -> HarryPotterCharacter:
    try:
        return harry_potter_resource.get_by_id(character_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/harry-potter", tags=["harry-potter"])
def create_harry_potter_character(new_data: HarryPotterCharacter) -> str:
    new_id = harry_potter_resource.post(new_data)
    return str(new_id)


@app.put("/harry-potter/{character_id}", tags=["harry-potter"])
def update_harry_potter_character(
    character_id: str, new_data: HarryPotterCharacter
) -> dict[str, int]:
    try:
        updated = harry_potter_resource.put(character_id, new_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"updated": updated}


@app.delete("/harry-potter/{character_id}", tags=["harry-potter"])
def delete_harry_potter_character(character_id: str) -> dict[str, int]:
    deleted = harry_potter_resource.delete(character_id)
    return {"deleted": deleted}


@app.get("/customers", tags=["customers"])
def get_customers(request: Request) -> CustomerCollection:
    return customer_resource.get(_query_template(request))


@app.post("/customers", tags=["customers"])
def create_customer(new_data: Customer) -> str:
    try:
        return str(customer_resource.post(new_data))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/customers/{customerNumber}", tags=["customers"])
def get_customer_by_id(customerNumber: int) -> Customer:
    try:
        return customer_resource.get_by_id(str(customerNumber))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/customers/{customerNumber}", tags=["customers"])
def update_customer(customerNumber: int, new_data: Customer) -> dict[str, int]:
    try:
        updated = customer_resource.put(str(customerNumber), new_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated == 0:
        try:
            customer_resource.get_by_id(str(customerNumber))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"updated": updated}


@app.delete("/customers/{customerNumber}", tags=["customers"])
def delete_customer(customerNumber: int) -> dict[str, int]:
    deleted = customer_resource.delete(str(customerNumber))
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No customer with id {customerNumber!r}")
    return {"deleted": deleted}


@app.get("/orders", tags=["orders"])
def get_orders(request: Request) -> OrderCollection:
    return order_resource.get(_query_template(request))


@app.post("/orders", tags=["orders"])
def create_order(new_data: Order) -> str:
    try:
        return str(order_resource.post(new_data))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/orders/{orderNumber}", tags=["orders"])
def get_order_by_id(orderNumber: int) -> Order:
    try:
        return order_resource.get_by_id(str(orderNumber))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/orders/{orderNumber}", tags=["orders"])
def update_order(orderNumber: int, new_data: Order) -> dict[str, int]:
    try:
        updated = order_resource.put(str(orderNumber), new_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated == 0:
        try:
            order_resource.get_by_id(str(orderNumber))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"updated": updated}


@app.delete("/orders/{orderNumber}", tags=["orders"])
def delete_order(orderNumber: int) -> dict[str, int]:
    deleted = order_resource.delete(str(orderNumber))
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No order with id {orderNumber!r}")
    return {"deleted": deleted}


@app.get("/orderdetails", tags=["orderdetails"])
def get_order_details(request: Request) -> OrderDetailsCollection:
    return order_details_resource.get(_query_template(request))


@app.post("/orderdetails", tags=["orderdetails"])
def create_order_detail(new_data: OrderDetail) -> str:
    try:
        return str(order_details_resource.post(new_data))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/orders/{orderNumber}/orderdetails", tags=["orderdetails"])
def get_order_details_by_order(orderNumber: int, request: Request) -> OrderDetailsCollection:
    template = _query_template(request)
    template["orderNumber"] = str(orderNumber)
    return order_details_resource.get(template)


@app.get("/orders/{orderNumber}/orderdetails/{productCode}", tags=["orderdetails"])
def get_order_detail_by_id(orderNumber: int, productCode: str) -> OrderDetail:
    try:
        return order_details_resource.get_by_id(
            {"orderNumber": orderNumber, "productCode": productCode}
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/orders/{orderNumber}/orderdetails/{productCode}", tags=["orderdetails"])
def update_order_detail(
    orderNumber: int, productCode: str, new_data: OrderDetail
) -> dict[str, int]:
    key = {"orderNumber": orderNumber, "productCode": productCode}
    try:
        updated = order_details_resource.put(key, new_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated == 0:
        try:
            order_details_resource.get_by_id(key)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"updated": updated}


@app.delete("/orders/{orderNumber}/orderdetails/{productCode}", tags=["orderdetails"])
def delete_order_detail(orderNumber: int, productCode: str) -> dict[str, int]:
    deleted = order_details_resource.delete(
        {"orderNumber": orderNumber, "productCode": productCode}
    )
    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No order detail with key ({orderNumber!r}, {productCode!r})",
        )
    return {"deleted": deleted}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)

