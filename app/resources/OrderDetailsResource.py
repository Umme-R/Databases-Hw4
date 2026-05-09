from __future__ import annotations

from decimal import Decimal
from typing import Optional, Union

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from .mysql_resource_common import build_mysql_config
from ..services.MySQLDataService import MySQLDataService


class OrderDetail(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: Decimal
    orderLineNumber: int


class OrderDetailsCollection(BaseModel):
    items: list[OrderDetail] = Field(default_factory=list)


class OrderDetailsResource(AbstractBaseResource):
    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        mysql_config = build_mysql_config("orderdetails", ["orderNumber", "productCode"])
        mysql_config.update(cfg)
        self._service = MySQLDataService(mysql_config)

    @staticmethod
    def _key(order_number: Union[int, str], product_code: str) -> dict[str, Union[str, int]]:
        return {"orderNumber": int(order_number), "productCode": product_code}

    def get(self, template: dict) -> OrderDetailsCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderDetailsCollection(
            items=[OrderDetail.model_validate(row) for row in rows]
        )

    def get_by_id(self, id: dict) -> OrderDetail:  # type: ignore[override]
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(
                "No order detail with key "
                f"({id.get('orderNumber')!r}, {id.get('productCode')!r})"
            )
        return OrderDetail.model_validate(row)

    def post(self, new_data: OrderDetail) -> str:
        return self._service.create(new_data.model_dump(exclude_none=True))

    def delete(self, id: dict) -> int:  # type: ignore[override]
        return self._service.deleteByPrimaryKey(id)

    def put(self, character_id: dict, new_data: OrderDetail) -> int:  # type: ignore[override]
        data = new_data.model_dump(exclude_none=True)
        data["orderNumber"] = int(character_id["orderNumber"])
        data["productCode"] = str(character_id["productCode"])
        return self._service.updateByPrimaryKey(character_id, data)
