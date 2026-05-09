from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union
from pydantic import BaseModel

class AbstractBaseResource(ABC):

    def __init__(self, config:dict) -> None:
        self._config = config

    @abstractmethod
    def get(self, template: dict) -> BaseModel:
        pass

    @abstractmethod
    def get_by_id(self, id: Union[str, dict]) -> BaseModel:
        pass

    @abstractmethod
    def post(self, new_data: BaseModel) -> str:
        pass

    @abstractmethod
    def delete(self, id: Union[str, dict]) -> int:
        pass

    @abstractmethod
    def put(self, character_id: Union[str, dict], new_data: BaseModel) -> int:
        pass


