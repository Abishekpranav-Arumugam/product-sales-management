# === Code updated here (send_event returns the pending Future) ===
import os
import json
from aiokafka import AIOKafkaProducer

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
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            await self.producer.start()

    async def stop(self):
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None

    async def send_event(self, topic: str, message: dict):
        if self.producer is None:
            raise RuntimeError("Kafka Producer is not initialized.")
        # send() returns a Future representing the pending write
        future = await self.producer.send(topic, message)
        return future


kafka_producer_client = KafkaProducerClient()
# =====================================================================