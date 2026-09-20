from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import io
import asyncio

from app.schemas.sale_schema import SaleCreate, SalePageResponse, SaleResponse
from app.service.sale_service import SaleService
from app.security.dependencies import (
    require_user,
    require_supervisor
)
from app.utils.kafka_producer import kafka_producer_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sales", tags=["Sales"])


def get_sale_service() -> SaleService:
    return SaleService()


async def log_metadata(future, event_message: dict):
    """
    Awaits the Kafka broker write confirmation in the background
    and prints the partition and offset on the producer side.
    """
    if future is None:
        logger.warning(
            "Kafka broker unavailable; skipped metadata confirmation.",
            extra={"product_id": event_message.get("product_id")},
        )
        return

    try:
        metadata = await future
        logger.info(
            "Sale event successfully acknowledged by Kafka",
            extra={
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
                "product_id": event_message["product_id"]
            }
        )
    except Exception as e:
        logger.error(
            "Asynchronous Kafka write confirmation failed",
            extra={"error": str(e)}
        )


@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Sale (Queue)",
    description=(
        "Delegates stock verification and database deduction to the service, "
        "then asynchronously publishes the event message to Kafka."
    ),
)
async def create_sale_queue(
    sale_data: SaleCreate,
    service: SaleService = Depends(get_sale_service),
    current_user=Depends(require_user),
):
    try:
        # 1. Delegate business logic and DB modifications to the service layer
        event_message = service.process_sale_queue(sale_data.model_dump())

        # 2. topic = sales_events
        future = await kafka_producer_client.send_event(
            "sale_events", event_message
        )

        # 3. Log immediate receipt memory
        if future is None:
            logger.warning(
                "Sale transaction processed without Kafka delivery confirmation.",
                extra={
                    "product_id": event_message.get("product_id"),
                    "remaining_quantity": event_message.get(
                        "remaining_quantity"
                    ),
                },
            )
        else:
            logger.info(
                "Sale event successfully queued",
                extra={
                    "product_id": event_message["product_id"],
                    "remaining_quantity": (
                        event_message["remaining_quantity"]
                    ),
                }
            )

        # 4. Monitor Kafka acknowledgement in the background
        asyncio.create_task(log_metadata(future, event_message))

        return {
            "status": "Accepted",
            "message": "Sale transaction placed in queue for processing."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # @router.post(
    #     "/",
    #     response_model=SaleResponse,
    #     summary="Create Sale",
    #     description="Create a new sale and reduce the product stock.",
    # )
    # def create_sale(
    #     sale_data: SaleCreate,
    #     service: SaleService = Depends(get_sale_service),
    #     current_user: Any = Depends(require_authenticated_user),
    # ) -> Any:

    #     try:

    #         return service.create_sale(sale_data.model_dump())

    #     except ValueError as e:

    #         raise HTTPException(status_code=400, detail=str(e))

    #     except Exception as e:

    #         raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report",
    summary="Download Sales Report",
    description=(
        "Download all sales records as a CSV file."
        "Access restricted to supervisors only."
    ),
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
    response_model=SalePageResponse,
    summary="Get All Sales",
    description="Returns all sales."
)
def get_all_sales(
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_supervisor),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
) -> dict[str, Any]:
    sales, total = service.get_sales_page(page, page_size)
    return {
        "items": sales,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get Sale",
    description="Returns a sale using its ID."
)
def get_sale(
    sale_id: int,
    service: SaleService = Depends(get_sale_service),
    current_user: Any = Depends(require_supervisor),
) -> Any:
    sale = service.get_sale(sale_id)
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale
