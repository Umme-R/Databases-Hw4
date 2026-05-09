from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from .mysql_resource_common import build_mysql_config
from ..services.MySQLDataService import MySQLDataService


class Order(BaseModel):
    orderNumber: Optional[int] = None
    orderDate: date
    requiredDate: date
    shippedDate: Optional[date] = None
    status: str
    comments: Optional[str] = None
    customerNumber: int


class OrderCollection(BaseModel):
    items: list[Order] = Field(default_factory=list)


class OrderResource(AbstractBaseResource):
    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        mysql_config = build_mysql_config("orders", ["orderNumber"])
        mysql_config.update(cfg)
        self._service = MySQLDataService(mysql_config)

    def get(self, template: dict) -> OrderCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderCollection(items=[Order.model_validate(row) for row in rows])

    def get_by_id(self, id: str) -> Order:  # noqa: A002
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No order with id {id!r}")
        return Order.model_validate(row)

    def post(self, new_data: Order) -> str:
        return self._service.create(new_data.model_dump(exclude_none=True))

    def delete(self, id: str) -> int:  # noqa: A002
        return self._service.deleteByPrimaryKey(id)

    def put(self, character_id: str, new_data: Order) -> int:
        data = new_data.model_dump(exclude_none=True)
        data["orderNumber"] = int(character_id)
        return self._service.updateByPrimaryKey(character_id, data)
