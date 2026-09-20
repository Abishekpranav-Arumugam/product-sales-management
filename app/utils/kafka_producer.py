import os
import json
from aiokafka import AIOKafkaProducer

from app.utils.logger import get_logger

logger = get_logger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)


class KafkaProducerClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.producer = None
        return cls._instance

    async def start(self):
        if self.producer is not None:
            return

        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

        try:
            await producer.start()
            self.producer = producer
        except Exception as exc:
            try:
                await producer.stop()
            except Exception:
                pass
            logger.warning(
                "Kafka producer unavailable; continuing without queueing.",
                extra={
                    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
                    "error": str(exc),
                }
            )

    async def stop(self):
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None

    async def send_event(self, topic: str, message: dict):
        if self.producer is None:
            logger.warning(
                "Kafka producer is not initialized; dropping event.",
                extra={"topic": topic, "message": message},
            )
            return None

        try:
            # send() returns a Future representing the pending write
            future = await self.producer.send(topic, message)
            return future
        except Exception as exc:
            logger.warning(
                "Kafka send failed; dropping event.",
                extra={"topic": topic, "message": message, "error": str(exc)},
            )
            return None


kafka_producer_client = KafkaProducerClient()
