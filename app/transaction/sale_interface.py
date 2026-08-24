from abc import ABC, abstractmethod
from typing import Any, Optional


class SaleInterface(ABC):

    @abstractmethod
    def create_sale(self, sale_data: dict[str, Any]) -> Any:
        pass

    @abstractmethod
    def get_all_sales(self) -> list[Any]:
        pass

    @abstractmethod
    def get_sale_by_id(self, sale_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def generate_sales_report(self) -> str:
        pass
