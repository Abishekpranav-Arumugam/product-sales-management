from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
from app.schemas.sale_schema import SaleCreate
from app.service.sale_service import SaleService
from app.schemas.sale_schema import SaleResponse
from app.security.dependencies import (
    require_authenticated_user,
    require_supervisor
)


router = APIRouter(prefix="/sales", tags=["Sales"])


def get_sale_service() -> SaleService:

    return SaleService()


@router.post(
    "/",
    response_model=SaleResponse,
    summary="Create Sale",
    description="Create a new sale and reduce the product stock.",
)
def create_sale(
    sale_data: SaleCreate,
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_authenticated_user),
) -> Any:

    try:

        return service.create_sale(sale_data.model_dump())

    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report",
    summary="Download Sales Report",
    description=(
        "Download all sales records as a CSV file."
        "Access restricted to supervisors only."),
)
def download_sales_report(
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_supervisor),
) -> StreamingResponse:
    try:
        csv_data = service.generate_sales_report()
        stream = io.StringIO(csv_data)

        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    "attachment; filename=sales_report.csv"
                )
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=list[SaleResponse],
    summary="Get All Sales",
    description="Returns all sales.")
def get_all_sales(
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_authenticated_user),
) -> list[Any]:

    return service.get_all_sales()


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get Sale",
    description="Returns a sale using its ID."
)
def get_sale(
    sale_id: int,
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_authenticated_user),
) -> Any:

    sale = service.get_sale(sale_id)

    if sale is None:

        raise HTTPException(status_code=404, detail="Sale not found")

    return sale
