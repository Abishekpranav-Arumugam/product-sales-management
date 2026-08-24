from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.dal.product_dal import ProductDAL


@staticmethod
def _make_product_data(i=1):
    return {
        "name": f"P{i}",
        "description": "desc",
        "price": 9.99,
        "quantity": 5,
        "category": "test",
    }


def setup_module() -> None:
    global engine, SessionLocal
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


def test_product_dal_crud() -> None:
    db = SessionLocal()
    dal = ProductDAL(db)

    # insert
    prod = dal.insert(_make_product_data())
    assert prod.id == 1
    assert prod.name == "P1"

    # get_by_id
    got = dal.get_by_id(1)
    assert got is not None and got.id == 1

    # get_all
    allp = dal.get_all()
    assert isinstance(allp, list) and len(allp) == 1

    # update
    updated = dal.update(
        1,
        {
            "name": "P1-up",
            "description": "d",
            "price": 5.0,
            "quantity": 2,
            "category": "c",
        },
    )
    assert updated.name == "P1-up"

    # update_quantity
    uq = dal.update_quantity(1, 10)
    assert uq.quantity == 10

    # delete
    deleted = dal.delete(1)
    assert deleted is True
    assert dal.get_by_id(1) is None

    db.close()
