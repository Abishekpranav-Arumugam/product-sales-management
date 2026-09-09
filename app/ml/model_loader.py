from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "random_forest_sales_model.pkl"
)


@lru_cache(maxsize=1)
def load_sales_model() -> Any:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Sales forecasting model was not found at {MODEL_PATH}"
        )
    return joblib.load(MODEL_PATH)
