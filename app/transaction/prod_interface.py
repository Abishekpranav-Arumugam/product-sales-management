from abc import ABC, abstractmethod
from typing import Any, Optional


class ProductInterface(ABC):

    @abstractmethod
    def add_product(self, product_data: dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def get_all_products(self) -> list[Any]:
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def update_product(self, product_id: int, product_data: dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def delete_product(self, product_id: int) -> bool:
        pass
