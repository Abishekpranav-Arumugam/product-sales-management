from fastapi import APIRouter, Depends, HTTPException

from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.service.product_service import ProductService
from app.schemas.product_schema import ProductResponse
from app.security.dependencies import require_supervisor

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service() -> ProductService:

    return ProductService()


@router.post("/", response_model=ProductResponse, summary="Create Product", description="Create a new product.")
def add_product(
    product_data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    current_user=Depends(require_supervisor),
):

    try:

        return service.add_product(product_data.model_dump())

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ProductResponse], summary="Get All Products", description="Returns all products.")
def get_all_products(
    service: ProductService = Depends(get_product_service),
    current_user=Depends(require_supervisor),
):

    return service.get_all_products()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get Product",
    description="Returns a product using its ID.",
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    current_user=Depends(require_supervisor),
):

    product = service.get_product(product_id)

    if product is None:

        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update Product",
    description="Updates an existing product.",
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    current_user=Depends(require_supervisor),
):

    try:

        product = service.update_product(product_id, product_data.model_dump())

        if product is None:

            raise HTTPException(status_code=404, detail="Product not found")

        return product

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{product_id}",
    summary="Delete Product",
    description="Deletes a product using its ID.",
)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    current_user=Depends(require_supervisor),
):

    try:

        deleted = service.delete_product(product_id)

        if not deleted:

            raise HTTPException(status_code=404, detail="Product not found")

        return {"message": "Product deleted successfully", "product_id": product_id}

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
