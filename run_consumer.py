# === Code updated here (Re-enabled real database writes) ===
import os
import asyncio
import json
from aiokafka import AIOKafkaConsumer

from app.service.sale_service import SaleService
from app.utils.logger import get_logger

logger = get_logger(__name__)
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"
)

async def consume_sales():
    consumer = AIOKafkaConsumer(
        "sale_events",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="sales_processors",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await consumer.start()
    logger.info("Sales Consumer Worker Daemon started successfully.")

    # Instantiate the Sale Service
    service = SaleService()

    try:
        async for message in consumer:
            sale_data = message.value
            
            # Log the extracted partition and offset from Kafka
            logger.info(
                "Pulled sale event from queue",
                extra={
                    "partition": message.partition,
                    "offset": message.offset,
                    "payload": sale_data
                }
            )

            try:
                # Call SaleService to write the record directly to PostgreSQL
                sale = service.create_sale(sale_data)
                logger.info(
                    "Asynchronously saved sale to database",
                    extra={
                        "sale_id": sale.id,
                        "product_id": sale_data["product_id"],
                        "partition": message.partition,
                        "offset": message.offset
                    }
                )
                await consumer.commit()
            except ValueError as e:
                logger.warning(
                    "Asynchronous sale failed validation",
                    extra={
                        "error": str(e),
                        "sale_data": sale_data,
                        "partition": message.partition,
                        "offset": message.offset
                    }
                )
                await consumer.commit()
            except Exception as e:
                logger.error(
                    "Asynchronous database write failed",
                    extra={
                        "error": str(e),
                        "sale_data": sale_data,
                        "partition": message.partition,
                        "offset": message.offset
                    }
                )
                raise

    except Exception as e:
        logger.error(
            "Consumer encountered an error",
            extra={"error": str(e)}
        )
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume_sales())
# ============================================================