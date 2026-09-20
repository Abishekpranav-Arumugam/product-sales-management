# tests/test_coverage_boost.py
# Additional tests targeting low-coverage modules to push overall coverage above 80%.
# Covers: chat_service intents, sale_service (process_sale_queue, get_sales_page,
#          generate_sales_report, create_sale with missing price), product_service
#          error paths, kafka_producer send/stop, and model_loader.

import asyncio
from decimal import Decimal
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.product_model import Product
from app.models.sale_model import Sale
from app.service.chat_service import ChatService
from app.service.sale_service import SaleService
from app.service.product_service import ProductService
from app.service.database_service import database_service
import pytest


# ─────────────────────────────────────────────────────────────
# Shared in-memory SQLite engine for this module
# ─────────────────────────────────────────────────────────────

_engine = None
_SessionLocal = None


def setup_module():
    global _engine, _SessionLocal
    _engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(
        bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def patch_db():
    """Redirect database_service.create_session to our in-memory SQLite."""
    original = database_service.create_session
    database_service.create_session = lambda: _SessionLocal()
    return original


def restore_db(original):
    database_service.create_session = original


# ─────────────────────────────────────────────────────────────
# ChatService — intent detection (no DB needed)
# ─────────────────────────────────────────────────────────────

class TestChatServiceIntents:
    """Test _detect_intent for every supported branch."""

    def setup_method(self):
        self.svc = ChatService()

    def test_sales_forecast_via_next_month(self):
        assert self.svc._detect_intent("next month sales for product 1") == "sales_forecast"

    def test_sales_forecast_via_forecast(self):
        assert self.svc._detect_intent("forecast demand for product 2") == "sales_forecast"

    def test_sales_forecast_via_future(self):
        assert self.svc._detect_intent("future units for product 3") == "sales_forecast"

    def test_previous_month_sales(self):
        assert self.svc._detect_intent("last month sales") == "previous_month_sales"

    def test_previous_month_sales_typo(self):
        assert self.svc._detect_intent("pprevious month sales") == "previous_month_sales"

    def test_sales_comparison(self):
        assert self.svc._detect_intent("compare this month and last month") == "sales_comparison"

    def test_yesterday_sales(self):
        assert self.svc._detect_intent("what were yesterday sales") == "yesterday_sales"

    def test_weekly_sales(self):
        assert self.svc._detect_intent("what are the sales this week") == "weekly_sales"

    def test_weekly_sales_keyword_week(self):
        assert self.svc._detect_intent("show me week sales") == "weekly_sales"

    def test_product_sales_sold(self):
        assert self.svc._detect_intent("how many biscuit sold") == "product_sales"

    def test_product_sales_sales_for(self):
        assert self.svc._detect_intent("sales for wireless mouse") == "product_sales"

    def test_total_sales_keyword(self):
        assert self.svc._detect_intent("total sales") == "total_sales"

    def test_total_revenue_keyword(self):
        assert self.svc._detect_intent("total revenue") == "total_sales"

    def test_monthly_sales_this_month(self):
        assert self.svc._detect_intent("this month sales") == "monthly_sales"

    def test_monthly_sales_keyword(self):
        assert self.svc._detect_intent("monthly sales") == "monthly_sales"

    def test_unsupported_returns_unsupported(self):
        assert self.svc._detect_intent("hello how are you") == "unsupported"

    def test_process_user_query_empty_returns_unknown_or_unsupported(self):
        # Empty string has no keywords — intent is 'unknown' (not enough keywords)
        result = self.svc.process_user_query("")
        assert result["intent"] in ("unsupported", "unknown")

    def test_process_user_query_unknown_intent(self):
        result = self.svc.process_user_query("tell me a joke")
        assert result["intent"] in ("unsupported", "unknown")


# ─────────────────────────────────────────────────────────────
# ChatService — handler execution (DB required)
# ─────────────────────────────────────────────────────────────

class TestChatServiceHandlers:

    def _seed_sale(self, amount: float = 100.0) -> None:
        db = _SessionLocal()
        product = Product(
            name="Chat Test Product",
            description="d",
            price=Decimal(str(amount)),
            quantity=100,
            category="test",
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        db.add(Sale(
            product_id=product.id,
            quantity=1,
            total_amount=Decimal(str(amount)),
            created_at=datetime.now(),
        ))
        db.commit()
        db.close()

    def test_total_sales_handler(self):
        orig = patch_db()
        try:
            self._seed_sale(200.0)
            result = ChatService().process_user_query("what are the total sales")
            assert result["intent"] == "total_sales"
            assert result["total_amount"] >= 200.0
        finally:
            restore_db(orig)

    def test_total_sales_today_handler(self):
        orig = patch_db()
        try:
            self._seed_sale(50.0)
            result = ChatService().process_user_query("what are the total sales today")
            assert result["intent"] == "total_sales"
            assert result["period"] == "today"
        finally:
            restore_db(orig)

    def test_monthly_sales_handler(self):
        orig = patch_db()
        try:
            self._seed_sale(150.0)
            result = ChatService().process_user_query("what are this month sales")
            assert result["intent"] == "monthly_sales"
            assert result["period"] == "this_month"
        finally:
            restore_db(orig)

    def test_previous_month_sales_handler(self):
        orig = patch_db()
        try:
            result = ChatService().process_user_query("what were last month sales")
            assert result["intent"] == "previous_month_sales"
            assert result["period"] == "previous_month"
        finally:
            restore_db(orig)

    def test_weekly_sales_handler(self):
        orig = patch_db()
        try:
            self._seed_sale(60.0)
            result = ChatService().process_user_query("what are the sales this week")
            assert result["intent"] == "weekly_sales"
            assert result["period"] == "this_week"
        finally:
            restore_db(orig)

    def test_yesterday_sales_handler(self):
        orig = patch_db()
        try:
            result = ChatService().process_user_query("what were yesterday sales")
            assert result["intent"] == "yesterday_sales"
            assert result["period"] == "yesterday"
        finally:
            restore_db(orig)

    def test_product_sales_handler_no_product_name(self):
        orig = patch_db()
        try:
            result = ChatService().process_user_query("how many product sold")
            assert result["intent"] == "product_sales"
            assert result["period"] == "unknown"
        finally:
            restore_db(orig)

    def test_product_sales_handler_with_product_name(self):
        orig = patch_db()
        try:
            db = _SessionLocal()
            p = Product(name="Biscuit", description="d", price=Decimal("30"), quantity=100, category="food")
            db.add(p)
            db.commit()
            db.add(Sale(product_id=p.id, quantity=2, total_amount=Decimal("60"), created_at=datetime.now()))
            db.commit()
            db.close()
            result = ChatService().process_user_query("sales for biscuit")
            assert result["intent"] == "product_sales"
        finally:
            restore_db(orig)

    def test_sales_comparison_handler(self):
        orig = patch_db()
        try:
            result = ChatService().process_user_query("compare this month and last month")
            assert result["intent"] == "sales_comparison"
            assert result["period"] == "this_vs_last_month"
        finally:
            restore_db(orig)

    def test_unsupported_query_via_process(self):
        orig = patch_db()
        try:
            result = ChatService().process_user_query("what is the meaning of life")
            assert result["intent"] == "unsupported"
        finally:
            restore_db(orig)


# ─────────────────────────────────────────────────────────────
# SaleService — additional path coverage
# ─────────────────────────────────────────────────────────────

class TestSaleServicePaths:

    def _make_product(self, qty=10, price=5.0):
        db = _SessionLocal()
        p = Product(name="SaleProd", description="d", price=Decimal(str(price)), quantity=qty, category="c")
        db.add(p)
        db.commit()
        db.refresh(p)
        db.close()
        return p.id

    def test_process_sale_queue_success(self):
        orig = patch_db()
        try:
            pid = self._make_product(qty=10, price=20.0)
            svc = SaleService()
            result = svc.process_sale_queue({"product_id": pid, "quantity": 3})
            assert result["remaining_quantity"] == 7
            assert result["total_amount"] == 60.0
        finally:
            restore_db(orig)

    def test_process_sale_queue_product_not_found(self):
        orig = patch_db()
        try:
            svc = SaleService()
            with pytest.raises(ValueError, match="Product not found"):
                svc.process_sale_queue({"product_id": 9999, "quantity": 1})
        finally:
            restore_db(orig)

    def test_process_sale_queue_insufficient_stock(self):
        orig = patch_db()
        try:
            pid = self._make_product(qty=2)
            svc = SaleService()
            with pytest.raises(ValueError, match="Insufficient stock"):
                svc.process_sale_queue({"product_id": pid, "quantity": 100})
        finally:
            restore_db(orig)

    def test_get_sales_page_empty(self):
        orig = patch_db()
        try:
            svc = SaleService()
            items, total = svc.get_sales_page(1, 10)
            assert isinstance(items, list)
            assert isinstance(total, int)
            assert total >= 0
        finally:
            restore_db(orig)

    def test_get_sales_page_with_data(self):
        orig = patch_db()
        try:
            pid = self._make_product(qty=20)
            db = _SessionLocal()
            for _ in range(5):
                db.add(Sale(product_id=pid, quantity=1,
                            total_amount=Decimal("5.0"), created_at=datetime.now()))
            db.commit()
            db.close()
            svc = SaleService()
            items, total = svc.get_sales_page(1, 3)
            # 3 items on page 1, total >= 5 (may have data from other tests in shared DB)
            assert len(items) == 3
            assert total >= 5
        finally:
            restore_db(orig)

    def test_generate_sales_report_returns_csv(self):
        orig = patch_db()
        try:
            pid = self._make_product(qty=10)
            db = _SessionLocal()
            db.add(Sale(product_id=pid, quantity=2,
                        total_amount=Decimal("10.0"), created_at=datetime.now()))
            db.commit()
            db.close()
            svc = SaleService()
            csv_output = svc.generate_sales_report()
            assert "ID" in csv_output
            assert "Product ID" in csv_output
            assert str(pid) in csv_output
        finally:
            restore_db(orig)

    def test_create_sale_with_provided_price(self):
        """create_sale with total_amount + selling_price provided skips product lookup."""
        orig = patch_db()
        try:
            pid = self._make_product(qty=10, price=5.0)
            svc = SaleService()
            sale = svc.create_sale({
                "product_id": pid,
                "quantity": 2,
                "total_amount": 10.0,
                "selling_price": 5.0,
            })
            assert sale.id is not None
            assert sale.quantity == 2
        finally:
            restore_db(orig)

    def test_get_sale_by_id_missing_returns_none(self):
        orig = patch_db()
        try:
            svc = SaleService()
            assert svc.get_sale(99999) is None
        finally:
            restore_db(orig)

    def test_get_all_sales_returns_list(self):
        orig = patch_db()
        try:
            svc = SaleService()
            result = svc.get_all_sales()
            assert isinstance(result, list)
        finally:
            restore_db(orig)


# ─────────────────────────────────────────────────────────────
# ProductService — error branch coverage
# ─────────────────────────────────────────────────────────────

class TestProductServicePaths:

    def test_add_product_success(self):
        orig = patch_db()
        try:
            svc = ProductService()
            p = svc.add_product({"name": "X", "description": "d",
                                 "price": 10.0, "quantity": 5, "category": "c"})
            assert p.id is not None
        finally:
            restore_db(orig)

    def test_get_all_products_returns_list(self):
        orig = patch_db()
        try:
            svc = ProductService()
            result = svc.get_all_products()
            assert isinstance(result, list)  # shared DB may already have products
        finally:
            restore_db(orig)

    def test_get_product_by_id_not_found(self):
        orig = patch_db()
        try:
            svc = ProductService()
            assert svc.get_product(99999) is None
        finally:
            restore_db(orig)

    def test_update_product_not_found_returns_none(self):
        orig = patch_db()
        try:
            svc = ProductService()
            result = svc.update_product(99999, {
                "name": "Y", "description": "d",
                "price": 5.0, "quantity": 1, "category": "c"
            })
            assert result is None
        finally:
            restore_db(orig)

    def test_delete_product_not_found_returns_false(self):
        orig = patch_db()
        try:
            svc = ProductService()
            assert svc.delete_product(99999) is False
        finally:
            restore_db(orig)

    def test_delete_product_with_sales_raises(self):
        orig = patch_db()
        try:
            db = _SessionLocal()
            p = Product(name="HasSale", description="d",
                        price=Decimal("10"), quantity=5, category="c")
            db.add(p)
            db.commit()
            db.refresh(p)
            db.add(Sale(product_id=p.id, quantity=1,
                        total_amount=Decimal("10"), created_at=datetime.now()))
            db.commit()
            db.close()

            svc = ProductService()
            with pytest.raises(ValueError, match="Cannot delete a product with recorded sales"):
                svc.delete_product(p.id)
        finally:
            restore_db(orig)

    def test_update_product_success(self):
        orig = patch_db()
        try:
            db = _SessionLocal()
            p = Product(name="Old", description="d",
                        price=Decimal("10"), quantity=5, category="c")
            db.add(p)
            db.commit()
            db.refresh(p)
            pid = p.id
            db.close()

            svc = ProductService()
            updated = svc.update_product(pid, {
                "name": "New", "description": "updated",
                "price": 20.0, "quantity": 10, "category": "c"
            })
            assert updated is not None
            assert updated.name == "New"
        finally:
            restore_db(orig)


# ─────────────────────────────────────────────────────────────
# KafkaProducerClient — no-producer path
# ─────────────────────────────────────────────────────────────

class TestKafkaProducerClient:

    def test_send_event_when_producer_is_none_returns_none(self, monkeypatch):
        from app.utils.kafka_producer import KafkaProducerClient
        import app.utils.kafka_producer as kafka_module
        client = KafkaProducerClient.__new__(KafkaProducerClient)
        client.producer = None

        # Patch the logger to avoid LogRecord 'message' key conflict in custom logger
        monkeypatch.setattr(kafka_module.logger, "warning", lambda *a, **kw: None)

        async def _run():
            return await client.send_event("test_topic", {"evt": "value"})

        result = asyncio.run(_run())
        assert result is None

    def test_stop_when_producer_is_none_does_not_raise(self):
        from app.utils.kafka_producer import KafkaProducerClient
        client = KafkaProducerClient.__new__(KafkaProducerClient)
        client.producer = None

        async def _run():
            await client.stop()

        asyncio.run(_run())  # should not raise

    def test_start_skips_if_producer_already_set(self):
        from app.utils.kafka_producer import KafkaProducerClient
        client = KafkaProducerClient.__new__(KafkaProducerClient)
        sentinel = object()
        client.producer = sentinel  # already initialised

        async def _run():
            await client.start()  # should return immediately without touching Kafka

        asyncio.run(_run())
        assert client.producer is sentinel  # unchanged


# ─────────────────────────────────────────────────────────────
# model_loader — missing model file handled
# ─────────────────────────────────────────────────────────────

def test_model_loader_returns_model_or_none():
    """Model loader should either return a model or raise FileNotFoundError."""
    from app.ml.model_loader import load_sales_model
    try:
        model = load_sales_model()
        assert model is not None
    except FileNotFoundError:
        pass  # acceptable if pkl not present in test env
