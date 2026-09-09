from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.service.sale_service import SaleService
from app.service.product_service import ProductService
from app.service.database_service import database_service


def setup_module() -> None:
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def test_sale_service_create_and_errors() -> None:
    orig = database_service.create_session
    database_service.create_session = lambda: SessionLocal()

    psvc = ProductService()
    prod = psvc.add_product(
        {"name": "SP", "description": "d", "price": 5.0,
            "quantity": 2, "category": "c"}
    )

    ssvc = SaleService()
    # successful sale
    sale = ssvc.create_sale({"product_id": prod.id, "quantity": 1})
    assert sale.id == 1

    # insufficient stock
    try:
        ssvc.create_sale({"product_id": prod.id, "quantity": 100})
        assert False, "expected ValueError"
    except ValueError:
        pass

    # product not found
    try:
        ssvc.create_sale({"product_id": 9999, "quantity": 1})
        assert False, "expected ValueError"
    except ValueError:
        pass

    database_service.create_session = orig
