# =============================================================================
# CHATBOT SUPPORTED QUERIES — COMPLETE REFERENCE
# Each handler is triggered by the keywords shown. Queries MUST be lowercase.
# =============================================================================
#
# ── 1. TOTAL SALES  (_handle_total_sales_query) ──────────────────────────────
#    Keywords: "total sales" | "total revenue" | "total amount" | "how much" + "sales"
#
#    "What are the total sales?"
#    "Show me the total revenue."
#    "What is the total amount from sales?"
#    "How much sales have we made?"
#    "How much is the total sales so far?"
#    "Give me the total sales."
#
#    Special — TODAY only (contains "today"):
#    "What are the total sales today?"
#    "How much did we sell today?"
#    "What is today's total sales?"
#
# ── 2. MONTHLY SALES  (_handle_monthly_sales_query) ──────────────────────────
#    Keywords: "monthly sales" | ("this" + "month" + "sales") | ("last" + "month" + "sales")
#             | (any month name + "month" + "sales")
#
#    "What are the monthly sales?"
#    "What are the sales for this month?"
#    "Show me this month's sales."
#    "How much did we sell this month?"
#    "What are the sales last month?"        ← only if "compare" is NOT in the question
#
# ── 3. PREVIOUS MONTH SALES  (_handle_previous_month_sales_query) ────────────
#    Keywords: ("previous month" | "last month") + "sales"
#    NOTE: "compare" must NOT be in the question (compare takes priority)
#
#    "What were last month's sales?"
#    "Show me previous month sales."
#    "What are the sales for last month?"
#    "How much did we sell last month?"
#    "What were the previous month sales?"
#
# ── 4. WEEKLY SALES  (_handle_weekly_sales_query) ────────────────────────────
#    Keywords: "this week" | "week"
#
#    "What are the sales this week?"
#    "How much did we sell this week?"
#    "Show me the weekly sales."
#    "What are the week's sales?"
#    "Give me this week's revenue."
#
# ── 5. YESTERDAY SALES  (_handle_yesterday_sales_query) ──────────────────────
#    Keywords: "yesterday"
#
#    "What were yesterday's sales?"
#    "How much did we sell yesterday?"
#    "Show me yesterday's revenue."
#    "What is the sales total for yesterday?"
#
# ── 6. PRODUCT SALES  (_handle_product_sales_query) ──────────────────────────
#    Keywords: "sold" | "sales for" | "sales of" | "product"
#    NOTE: Product name must match a name in the database (case-insensitive substring).
#    Returns THIS MONTH's sales for the named product.
#
#    "What are the sales for Wireless Mouse?"
#    "How much did HP Pavillion sell?"
#    "Sales of Notebook this month."
#    "How many units were sold for Mechanical Keyboard?"
#    "What is the sales for Potato Chips?"
#    "Show me the sales of USB-C Charger."
#
#
# ── 8. SALES COMPARISON  (_handle_sales_comparison_query) ────────────────────
#    Keywords: "compare" + ("this month" | "last month")
#
#    "Compare this month and last month."
#    "Compare last month with this month."
#    "Can you compare this month's sales to last month?"
#    "Compare sales this month vs last month."
#
#
# ── 11. SALES FORECAST  (_handle_sales_forecast_query) ───────────────────────
#    Keywords: ("next month" | "future" | "forecast") + ("sales" | "demand" | "units")
#    NOTE: Product name OR product ID must be included in the question.
#
#    Using product name (must match DB name, case-insensitive substring):
#    "What is the forecast for Biscuit?"
#    "Forecast sales for Wireless Mouse next month."
#    "What is the future demand for HP Pavillion?"
#    "How many units will Notebook sell next month?"
#    "Predict next month sales for Potato Chips."
#    "What is the forecast demand for Mechanical Keyboard?"
#    "Future sales for USB-C Charger."
#    "Next month demand for Bluetooth Headphones."
#
#    Using product ID (any number in the question is tried as product ID first):
#    "Forecast sales for product 6."
#    "What is the forecast for product 1?"
#    "Next month demand for product 11."
#    "Future units for 7."
#
# =============================================================================
from datetime import datetime, timedelta
import re

from sqlalchemy.orm import Session

from app.models.product_model import Product
from app.models.sale_model import Sale
from app.ml.forecast_service import ForecastService
from app.service.database_service import database_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    def __init__(self) -> None:
        self.forecast_service = ForecastService()

    def process_user_query(self, question: str) -> dict:
        normalized = (question or "").strip().lower()

        if not normalized:
            return {
                "intent": "unknown",
                "period": "unknown",
                "total_amount": None,
                "response": (
                    "I couldn't understand your question. Please ask about "
                    "sales totals, monthly sales, weekly sales, or "
                    "product sales."
                ),
            }

        intent = self._detect_intent(normalized)
        handlers = {
            "sales_forecast": self._handle_sales_forecast_query,
            "previous_month_sales": self._handle_previous_month_sales_query,
            "monthly_sales": self._handle_monthly_sales_query,
            "total_sales": self._handle_total_sales_query,
            "weekly_sales": self._handle_weekly_sales_query,
            "yesterday_sales": self._handle_yesterday_sales_query,
            "product_sales": self._handle_product_sales_query,
            "sales_comparison": self._handle_sales_comparison_query,

        }

        handler = handlers.get(intent)
        if handler is None:
            return {
                "intent": "unsupported",
                "period": "unknown",
                "total_amount": None,
                "response": (
                    "I can help with monthly sales, total sales, weekly "
                    "sales, product sales, comparisons, and trends."
                ),
            }

        return handler(normalized)

    def _detect_intent(self, question: str) -> str:
        if (
            (
                "next month" in question
                or "future" in question
                or "forecast" in question
            )
            and (
                "sales" in question
                or "demand" in question
                or "units" in question
            )
        ):
            return "sales_forecast"

        if (
            (
                "previous month" in question
                or "pprevious month" in question
                or "last month" in question
            )
            and "sales" in question
        ):
            return "previous_month_sales"

        if "compare" in question and (
            "this month" in question or "last month" in question
        ):
            return "sales_comparison"

        if "yesterday" in question:
            return "yesterday_sales"

        if "this week" in question or "week" in question:
            return "weekly_sales"

        if (
            "sold" in question
            or "sales for" in question
            or "sales of" in question
            or "product" in question
        ):
            return "product_sales"

        if (
            "monthly sales" in question
            or (
                "month" in question
                and "sales" in question
                and (
                    "this" in question
                    or "last" in question
                    or self._month_name_in_question(question)
                )
            )
        ):
            return "monthly_sales"

        if (
            "total sales" in question
            or "total revenue" in question
            or "total amount" in question
            or "how much" in question and "sales" in question
        ):
            return "total_sales"

        return "unsupported"

    def _handle_previous_month_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            current_month_start = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if current_month_start.month == 1:
                previous_month_start = datetime(
                    current_month_start.year - 1, 12, 1
                )
            else:
                previous_month_start = datetime(
                    current_month_start.year,
                    current_month_start.month - 1,
                    1,
                )

            records = self._get_sales_records(
                db,
                start=previous_month_start,
                end=current_month_start,
            )
            total_amount = sum(float(item.total_amount) for item in records)
            label = previous_month_start.strftime("%B %Y")
            response = (
                f"The total sales for {label} are "
                f"{self._to_currency(total_amount)}."
            )
            return {
                "intent": "previous_month_sales",
                "period": "previous_month",
                "total_amount": total_amount,
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_sales_forecast_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            product = self._find_forecast_product(db, question)
            if product is None:
                raise ValueError(
                    "Please include a product name or product ID in the "
                    "forecast question."
                )

            forecast = self.forecast_service.forecast_product(db, product.id)
            supplier_text = (
                " Buy from "
                f"{forecast['recommended_supplier']['supplier_name']}."
                if forecast["recommended_supplier"]
                else " No supplier is mapped to this product."
            )
            response = (
                f"{forecast['product_name']} is forecast to sell "
                f"{forecast['predicted_demand']} units in "
                f"{forecast['forecast_month']}. Current stock is "
                f"{forecast['current_stock']}; recommended purchase quantity "
                f"is {forecast['recommended_purchase_quantity']}."
                f"{supplier_text}"
            )
            return {
                "intent": "sales_forecast",
                "period": forecast["forecast_month"],
                "total_amount": None,
                "response": response,
                **forecast,
            }
        finally:
            db.close()

    def _find_forecast_product(
        self, db: Session, question: str
    ) -> Product | None:
        product_id_match = re.search(r"\b\d+\b", question)
        if product_id_match:
            product = db.get(Product, int(product_id_match.group(0)))
            if product is not None:
                return product

        products = db.query(Product).order_by(Product.name.asc()).all()
        return next(
            (product for product in products if product.name.lower() in question),
            None,
        )

    def _month_name_in_question(self, question: str) -> bool:
        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        return any(month in question for month in months)

    def _get_sales_records(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        product_name: str | None = None,
    ) -> list[Sale]:
        query = db.query(Sale)

        if start is not None:
            query = query.filter(Sale.created_at >= start)
        if end is not None:
            query = query.filter(Sale.created_at < end)

        if product_name:
            product = (
                db.query(Product)
                .filter(Product.name.ilike(f"%{product_name}%"))
                .first()
            )
            if product is None:
                return []
            query = query.filter(Sale.product_id == product.id)

        return query.order_by(Sale.created_at.asc()).all()

    def _to_currency(self, value: float) -> str:
        return f"${value:,.2f}"

    def _handle_monthly_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            records = self._get_sales_records(db, start=start)
            total_amount = sum(float(item.total_amount) for item in records)

            response = (
                f"The total sales for this month are "
                f"{self._to_currency(total_amount)}."
            )

            logger.info(
                "Chatbot query processed",
                extra={
                    "intent": "monthly_sales",
                    "period": "this_month",
                    "total_amount": total_amount,
                },
            )

            return {
                "intent": "monthly_sales",
                "period": "this_month",
                "total_amount": float(total_amount),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_total_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            today = datetime.now()
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)

            if "today" in question:
                records = self._get_sales_records(db, start=start_of_day)
                period = "today"
            else:
                records = self._get_sales_records(db)
                period = "all_time"

            total_amount = sum(float(item.total_amount) for item in records)
            response = (
                f"The total sales for {period} are "
                f"{self._to_currency(total_amount)}."
            )

            return {
                "intent": "total_sales",
                "period": period,
                "total_amount": float(total_amount),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_weekly_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            records = self._get_sales_records(db, start=start_of_week)
            total_amount = sum(float(item.total_amount) for item in records)

            response = (
                f"The sales for this week are {self._to_currency(total_amount)}."
            )

            return {
                "intent": "weekly_sales",
                "period": "this_week",
                "total_amount": float(total_amount),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_yesterday_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            day_start = yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            records = self._get_sales_records(
                db, start=day_start, end=day_end
            )
            total_amount = sum(float(item.total_amount) for item in records)

            response = (
                f"The sales for yesterday were "
                f"{self._to_currency(total_amount)}."
            )

            return {
                "intent": "yesterday_sales",
                "period": "yesterday",
                "total_amount": float(total_amount),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_product_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            products = db.query(Product).order_by(Product.name.asc()).all()
            product = next(
                (item for item in products if item.name.lower() in question),
                None,
            )
            product_name = product.name if product else None

            records = self._get_sales_records(
                db,
                start=datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                product_name=product_name,
            )
            total_amount = sum(float(item.total_amount) for item in records)

            if product_name:
                response = (
                    f"Sales for {product_name} this month are "
                    f"{self._to_currency(total_amount)}."
                )
                period = "this_month"
            else:
                response = (
                    "I can help with product sales if you mention a product "
                    "name, for example: 'How much did biscuit sell this month?'"
                )
                period = "unknown"
                total_amount = 0.0

            return {
                "intent": "product_sales",
                "period": period,
                "total_amount": float(total_amount),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()

    def _handle_sales_comparison_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            current_month_start = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if now.month == 1:
                previous_month_start = datetime(now.year - 1, 12, 1)
            else:
                previous_month_start = datetime(now.year, now.month - 1, 1)

            if now.month == 12:
                previous_month_end = datetime(now.year + 1, 1, 1)
            else:
                previous_month_end = datetime(now.year, now.month, 1)

            current_records = self._get_sales_records(db, start=current_month_start)
            previous_records = self._get_sales_records(
                db, start=previous_month_start, end=previous_month_end
            )

            current_total = sum(float(item.total_amount) for item in current_records)
            previous_total = sum(float(item.total_amount) for item in previous_records)
            difference = current_total - previous_total

            response = (
                f"This month: {self._to_currency(current_total)}. "
                f"Last month: {self._to_currency(previous_total)}. "
                f"Difference: {self._to_currency(difference)}."
            )

            return {
                "intent": "sales_comparison",
                "period": "this_vs_last_month",
                "total_amount": float(current_total),
                "response": response,
                "records": len(current_records),
            }
        finally:
            db.close()
