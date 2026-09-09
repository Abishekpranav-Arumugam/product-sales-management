from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ..., min_length=1, description="User question to process"
    )


class RecommendedSupplier(BaseModel):
    supplier_id: int
    supplier_name: str


class ChatResponse(BaseModel):
    intent: str
    period: str
    total_amount: float | None = None
    response: str
    product_id: int | None = None
    product_name: str | None = None
    forecast_month: str | None = None
    predicted_demand: int | None = None
    current_stock: int | None = None
    recommended_purchase_quantity: int | None = None
    recommended_supplier: RecommendedSupplier | None = None
