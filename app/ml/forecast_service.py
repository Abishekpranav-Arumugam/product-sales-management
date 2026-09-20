from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.ml.model_loader import load_sales_model
from app.models.product_model import Product
from app.models.product_supplier_model import ProductSupplier
from app.models.purchase_model import Purchase
from app.models.sale_model import Sale
from app.models.supplier_model import Supplier


FEATURE_COLUMNS = [
    "product_id",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_std_3",
    "rolling_std_6",
    "month_number",
]


class ForecastService:
    def forecast_product(self, db: Session, product_id: int) -> dict[str, Any]:
        product = db.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} was not found")

        features, forecast_period = self._build_features(db, product_id)
        prediction = float(load_sales_model().predict(features)[0])
        predicted_demand = max(0, round(prediction))
        current_stock = int(product.quantity)
        recommended_quantity = max(predicted_demand - current_stock, 0)
        supplier = self._recommend_supplier(db, product_id)

        return {
            "product_id": product.id,
            "product_name": product.name,
            "forecast_month": forecast_period.strftime("%Y-%m"),
            "predicted_demand": predicted_demand,
            "current_stock": current_stock,
            "recommended_purchase_quantity": recommended_quantity,
            "recommended_supplier": supplier,
        }

    def _build_features(
        self, db: Session, product_id: int
    ) -> tuple[pd.DataFrame, pd.Period]:
        records = (
            db.query(Sale.created_at, Sale.quantity)
            .filter(Sale.product_id == product_id)
            .order_by(Sale.created_at.asc())
            .all()
        )
        if not records:
            raise ValueError(
                f"Product {product_id} does not have enough sales history "
                "for a forecast"
            )

        history = pd.DataFrame(
            {
                "created_at": [record.created_at for record in records],
                "quantity": [record.quantity for record in records],
            }
        )
        history["month"] = pd.to_datetime(
            history["created_at"]
        ).dt.to_period("M")
        monthly = history.groupby("month")["quantity"].sum().sort_index()
        latest_month = monthly.index.max()
        first_month = monthly.index.min()
        if (latest_month - first_month).n + 1 < 6:
            raise ValueError(
                "At least six calendar months of sales history are required "
                "for a forecast"
            )

        complete_index = pd.period_range(first_month, latest_month, freq="M")
        monthly = monthly.reindex(complete_index, fill_value=0).astype(float)
        recent = monthly.loc[latest_month - 5:latest_month]
        if len(recent) < 6:
            raise ValueError(
                "At least six calendar months of sales history are required "
                "for a forecast"
            )

        row = {
            "product_id": product_id,
            "lag_1": recent.iloc[-1],
            "lag_2": recent.iloc[-2],
            "lag_3": recent.iloc[-3],
            "lag_6": recent.iloc[-6],
            "rolling_mean_3": recent.iloc[-3:].mean(),
            "rolling_mean_6": recent.mean(),
            "rolling_std_3": recent.iloc[-3:].std(),
            "rolling_std_6": recent.std(),
            "month_number": (latest_month + 1).month,
        }
        return pd.DataFrame([row], columns=FEATURE_COLUMNS), latest_month + 1

    def _recommend_supplier(
        self, db: Session, product_id: int
    ) -> dict[str, Any] | None:
        supplier_ids = (
            db.query(ProductSupplier.supplier_id)
            .filter(ProductSupplier.product_id == product_id)
            .all()
        )
        if not supplier_ids:
            return None

        candidates = []
        for (supplier_id,) in supplier_ids:
            supplier = db.get(Supplier, supplier_id)
            purchases = (
                db.query(Purchase)
                .filter(
                    Purchase.product_id == product_id,
                    Purchase.supplier_id == supplier_id,
                )
                .all()
            )
            average_price = (
                sum(
                    float(item.purchase_price) for item in purchases
                ) / len(purchases)
                if purchases
                else float("inf")
            )
            total_quantity = sum(item.quantity for item in purchases)
            latest_purchase = max(
                (item.purchased_at for item in purchases),
                default=datetime.min,
            )
            candidates.append(
                {
                    "supplier_id": supplier_id,
                    "supplier_name": supplier.name,
                    "average_purchase_price": average_price,
                    "total_quantity_supplied": total_quantity,
                    "purchase_count": len(purchases),
                    "latest_purchase": latest_purchase,
                }
            )

        candidates.sort(
            key=lambda item: (
                item["average_purchase_price"],
                -item["total_quantity_supplied"],
                -item["purchase_count"],
                -item["latest_purchase"].timestamp()
                if item["latest_purchase"] != datetime.min
                else 0,
            )
        )
        selected = candidates[0]
        return {
            "supplier_id": selected["supplier_id"],
            "supplier_name": selected["supplier_name"],
        }
