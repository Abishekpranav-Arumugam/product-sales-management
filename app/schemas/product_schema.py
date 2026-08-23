from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):

    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the product"
    )

    description: str | None = Field(
        default=None, max_length=500, description="Product description"
    )

    price: Decimal = Field(..., gt=0, description="Product price")

    quantity: int = Field(..., ge=0, description="Available product quantity")

    category: str = Field(
        ..., min_length=1, max_length=100, description="Product category"
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):

    model_config = ConfigDict(from_attributes=True)

    id: int
