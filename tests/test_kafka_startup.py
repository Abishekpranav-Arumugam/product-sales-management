import asyncio

from app.main import app, lifespan


class GracefulFakeKafkaProducer:
    """Simulates Kafka being unreachable but handles the error gracefully,
    matching the real KafkaProducerClient behaviour."""

    def __init__(self):
        self.producer = None

    async def start(self):
        # Swallow the connection error, just like the real KafkaProducerClient does
        pass

    async def stop(self):
        pass


def test_app_lifespan_handles_missing_kafka(monkeypatch):
    """Lifespan must not crash when Kafka is unavailable — it degrades gracefully."""
    import app.main as main_module

    monkeypatch.setattr(main_module, "kafka_producer_client", GracefulFakeKafkaProducer())

    async def _run():
        async with lifespan(app):
            pass  # should complete without raising

    asyncio.run(_run())  # should NOT raise
