from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ml import forecast_service
from app.ml.forecast_service import FEATURE_COLUMNS, ForecastService
from app.models.base import Base
from app.models.product_model import Product
from app.models.product_supplier_model import ProductSupplier
from app.models.purchase_model import Purchase
from app.models.sale_model import Sale
from app.models.supplier_model import Supplier


class StubModel:
    def __init__(self):
        self.features = None

    def predict(self, features):
        self.features = features
        return [56]


def test_forecast_features_inventory_and_supplier_ranking(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    model = StubModel()
    monkeypatch.setattr(forecast_service, "load_sales_model", lambda: model)

    product = Product(
        name="HP Pavillion",
        description="Laptop",
        price=Decimal("1000.00"),
        quantity=20,
        category="Computers",
    )
    cheaper = Supplier(name="Supp X")
    expensive = Supplier(name="Supp Y")
    db.add_all([product, cheaper, expensive])
    db.commit()
    db.refresh(product)
    db.refresh(cheaper)
    db.refresh(expensive)

    for month in range(1, 7):
        db.add(
            Sale(
                product_id=product.id,
                quantity=month * 10,
                total_amount=Decimal("100.00"),
                created_at=datetime(2026, month, 15),
            )
        )
    db.add_all(
        [
            ProductSupplier(product_id=product.id, supplier_id=cheaper.id),
            ProductSupplier(product_id=product.id, supplier_id=expensive.id),
            Purchase(
                product_id=product.id,
                supplier_id=cheaper.id,
                quantity=100,
                purchase_price=Decimal("10.00"),
                purchased_at=datetime(2026, 7, 1),
            ),
            Purchase(
                product_id=product.id,
                supplier_id=expensive.id,
                quantity=100,
                purchase_price=Decimal("20.00"),
                purchased_at=datetime(2026, 7, 1),
            ),
        ]
    )
    db.commit()

    result = ForecastService().forecast_product(db, product.id)

    assert list(model.features.columns) == FEATURE_COLUMNS
    assert model.features.iloc[0]["lag_1"] == 60
    assert model.features.iloc[0]["lag_6"] == 10
    assert model.features.iloc[0]["month_number"] == 7
    assert result["forecast_month"] == "2026-07"
    assert result["predicted_demand"] == 56
    assert result["current_stock"] == 20
    assert result["recommended_purchase_quantity"] == 36
    assert result["recommended_supplier"] == {
        "supplier_id": cheaper.id,
        "supplier_name": "Supp X",
    }

    db.close()
    engine.dispose()
