from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.dal.product_dal import ProductDAL
from app.dal.sale_dal import SaleDAL


def _make_product_data():
    return {
        "name": "Prod",
        "description": "d",
        "price": 10.0,
        "quantity": 20,
        "category": "cat",
    }


def setup_module() -> None:
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def test_sale_dal_insert_and_get() -> None:
    db = SessionLocal()
    p_dal = ProductDAL(db)
    s_dal = SaleDAL(db)

    p = p_dal.insert(_make_product_data())
    db.commit()

    sale = s_dal.insert(
        {"product_id": p.id, "quantity": 2, "total_amount": 20.0})
    assert sale.id == 1
    assert sale.product_id == p.id
    assert sale.product.id == p.id
    db.expire(p, ["sales"])
    assert len(p.sales) == 1
    assert p.sales[0].id == sale.id

    all_sales = s_dal.get_all()
    assert len(all_sales) == 1

    got = s_dal.get_by_id(1)
    assert got is not None and got.id == 1

    db.close()
