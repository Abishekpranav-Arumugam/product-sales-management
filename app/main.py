from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.controllers.auth_control import router as auth_router
from app.controllers.chat_control import router as chat_router
from app.controllers.prod_control import router as product_router
from app.controllers.sale_control import router as sale_router
from app.utils.kafka_producer import kafka_producer_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await kafka_producer_client.start()
    yield
    await kafka_producer_client.stop()


app = FastAPI(
    title="Product Management API",
    description="Product and Sales Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(product_router)
app.include_router(sale_router)
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/", tags=["System"])
def root():
    return {"message": "Product Management API is running"}
