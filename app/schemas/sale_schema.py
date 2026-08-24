from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class SaleCreate(BaseModel):

    product_id: int = Field(..., gt=0,
                            description="ID of the product being sold")

    quantity: int = Field(..., gt=0, description="Quantity to sell")


class SaleResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    total_amount: Decimal
