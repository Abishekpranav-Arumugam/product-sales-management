from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.product_model import Product
from app.models.sale_model import Sale
from app.service.chat_service import ChatService
from app.service.database_service import database_service


def setup_module() -> None:
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def test_chat_service_monthly_sales_for_this_month() -> None:
    original_session_factory = database_service.create_session
    database_service.create_session = lambda: SessionLocal()

    try:
        db = SessionLocal()
        product = Product(
            name="Keyboard",
            description="Mechanical keyboard",
            price=Decimal("25.00"),
            quantity=50,
            category="Accessories",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        db.add_all(
            [
                Sale(
                    product_id=product.id,
                    quantity=2,
                    total_amount=Decimal("50.00"),
                    created_at=datetime.now(),
                ),
                Sale(
                    product_id=product.id,
                    quantity=1,
                    total_amount=Decimal("25.00"),
                    created_at=datetime.now(),
                ),
            ]
        )
        db.commit()
        db.close()

        service = ChatService()
        # "monthly sales" keyword directly hits monthly_sales intent without ambiguity
        result = service.process_user_query("monthly sales")

        assert result["intent"] == "monthly_sales"
        assert result["period"] == "this_month"
        assert result["total_amount"] >= 75.0
        assert "this month" in result["response"].lower()
    finally:
        database_service.create_session = original_session_factory


def test_chat_service_detects_forecast_prompts() -> None:
    service = ChatService()

    assert (
        service._detect_intent(
            "what are the forecast sales for product 1 next month?"
        )
        == "sales_forecast"
    )
    assert (
        service._detect_intent(
            "how many units of product 1 will sell next month?"
        )
        == "sales_forecast"
    )


def test_chat_service_detects_previous_month_prompts() -> None:
    service = ChatService()

    assert (
        service._detect_intent("what is the previous month sales?")
        == "previous_month_sales"
    )
    assert (
        service._detect_intent("what were the last month sales?")
        == "previous_month_sales"
    )
    assert (
        service._detect_intent("what was the previous month sales?")
        == "previous_month_sales"
    )


def test_chat_service_finds_product_by_id() -> None:
    original_session_factory = database_service.create_session
    database_service.create_session = lambda: SessionLocal()

    try:
        with database_service.create_session() as db:
            product = Product(
                name="HP Pavillion",
                description="Laptop",
                price=Decimal("1000.00"),
                quantity=20,
                category="Computers",
            )
            db.add(product)
            db.commit()
            db.refresh(product)

            found = ChatService()._find_forecast_product(
                db,
                f"what are the forecast sales for product {product.id} next month?",
            )

            assert found.id == product.id
    finally:
        database_service.create_session = original_session_factory
