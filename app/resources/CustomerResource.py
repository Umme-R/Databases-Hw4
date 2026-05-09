from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from .mysql_resource_common import build_mysql_config
from ..services.MySQLDataService import MySQLDataService


class Customer(BaseModel):
    customerNumber: Optional[int] = None
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str
    salesRepEmployeeNumber: Optional[int] = None
    creditLimit: Optional[Decimal] = None


class CustomerCollection(BaseModel):
    items: list[Customer] = Field(default_factory=list)


class CustomerResource(AbstractBaseResource):
    def __init__(self, config: Optional[dict] = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        mysql_config = build_mysql_config("customers", ["customerNumber"])
        mysql_config.update(cfg)
        self._service = MySQLDataService(mysql_config)

    def get(self, template: dict) -> CustomerCollection:
        rows = self._service.retrieveByTemplate(template)
        return CustomerCollection(items=[Customer.model_validate(row) for row in rows])

    def get_by_id(self, id: str) -> Customer:  # noqa: A002
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No customer with id {id!r}")
        return Customer.model_validate(row)

    def post(self, new_data: Customer) -> str:
        return self._service.create(new_data.model_dump(exclude_none=True))

    def delete(self, id: str) -> int:  # noqa: A002
        return self._service.deleteByPrimaryKey(id)

    def put(self, character_id: str, new_data: Customer) -> int:
        data = new_data.model_dump(exclude_none=True)
        data["customerNumber"] = int(character_id)
        return self._service.updateByPrimaryKey(character_id, data)
