from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.service.product_service import ProductService
from app.service.database_service import database_service

def setup_module():
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def test_product_service_add_and_get():
    # monkeypatch database_service to use in-memory session
    orig = database_service.create_session
    database_service.create_session = lambda: SessionLocal()

    svc = ProductService()
    prod = svc.add_product(
        {
            "name": "SProd",
            "description": "d",
            "price": 12.5,
            "quantity": 3,
            "category": "c",
        }
    )
    assert prod.id == 1

    allp = svc.get_all_products()
    assert len(allp) == 1

    got = svc.get_product(1)
    assert got is not None

    # restore
    database_service.create_session = orig


def test_update_and_delete_product_branches():
    orig = database_service.create_session
    database_service.create_session = lambda: SessionLocal()

    svc = ProductService()

    # updating non-existent product should return None
    res = svc.update_product(
        9999,
        {"name": "x", "description": "d", "price": 1.0, "quantity": 1, "category": "c"},
    )
    assert res is None

    # create then delete
    prod = svc.add_product(
        {
            "name": "ToDel",
            "description": "d",
            "price": 3.0,
            "quantity": 1,
            "category": "c",
        }
    )
    assert svc.delete_product(prod.id) is True
    assert svc.delete_product(9999) is False

    database_service.create_session = orig
