from fastapi import FastAPI

from app.controllers.prod_control import router as product_router
from app.controllers.sale_control import router as sale_router
from app.controllers.auth_control import router as auth_router


app = FastAPI(
    title="Product Management API",
    description="Product and Sales Management System",
    version="1.0.0",
)


app.include_router(product_router)
app.include_router(sale_router)
app.include_router(auth_router)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:

    return {"message": "Product Management API is running"}


# edit: trigger pre-commit tests
