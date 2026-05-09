from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

class AbstractBaseDataService(ABC):

    def __init__(self, config: dict) -> None:
        self.config = config

    @abstractmethod
    def retrieveByPrimaryKey(self, primary_key: Union[str, dict]) -> dict:
        pass

    @abstractmethod
    def retrieveByTemplate(self, template: dict) -> list[dict]:
        pass

    @abstractmethod
    def create(self, payload: dict) -> str:
        pass

    @abstractmethod
    def updateByPrimaryKey(self, primary_key: Union[str, dict], payload: dict) -> int:
        pass

    @abstractmethod
    def deleteByPrimaryKey(self, primary_key: Union[str, dict]) -> int:
        pass
