# 1. What are the total sales?
# 2. How much are the sales today?
# 3. What are the sales for this month?
# 4. How much did we sell this week?
# 5. What were yesterday's sales?
# 6. How much did Biscuit sell this month?
# 7. What were the sales in August?
# 8. Compare this month and last month.
# 9. What is the sales trend?
# 10. What is the average sale value?
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
            "filtered_monthly_sales": self._handle_filtered_monthly_query,
            "sales_comparison": self._handle_sales_comparison_query,
            "sales_trend": self._handle_sales_trend_query,
            "average_sales": self._handle_average_sales_query,
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

        if "trend" in question:
            return "sales_trend"

        if "average" in question or "avg" in question:
            return "average_sales"

        if "yesterday" in question:
            return "yesterday_sales"

        if "this week" in question or "week" in question:
            return "weekly_sales"

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

        if (
            "sales for" in question
            or "sales of" in question
            or "sold" in question
            or "product" in question
        ):
            return "product_sales"

        if "month" in question and "sales" in question:
            return "filtered_monthly_sales"

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
            product_name = None
            for phrase in ["for ", "of ", "product "]:
                if phrase in question:
                    try:
                        product_name = question.split(phrase, 1)[1].strip()
                        product_name = product_name.split(" ", 1)[0]
                    except IndexError:
                        product_name = None
                    break

            if product_name in {"this", "month", "week", "today", "yesterday"}:
                product_name = None

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

    def _handle_filtered_monthly_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            month_name = None
            for name in [
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
            ]:
                if name in question:
                    month_name = name
                    break

            if month_name is None:
                month_name = "this month"

            if month_name == "this month":
                start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end = start.replace(day=28) + timedelta(days=4)
                end = end.replace(day=1)
                label = "this month"
            else:
                month_index = [
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
                ].index(month_name) + 1
                year = datetime.now().year
                start = datetime(year, month_index, 1)
                end = datetime(year, month_index % 12 + 1, 1) if month_index < 12 else datetime(year + 1, 1, 1)
                label = month_name.title()

            records = self._get_sales_records(db, start=start, end=end)
            total_amount = sum(float(item.total_amount) for item in records)

            response = (
                f"The sales for {label} were {self._to_currency(total_amount)}."
            )

            return {
                "intent": "filtered_monthly_sales",
                "period": label,
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

    def _handle_sales_trend_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            month_totals = []

            for index in range(6):
                month_start = now.replace(day=1)
                month_start = month_start.replace(
                    month=((now.month - index - 1) % 12) + 1,
                    year=now.year if now.month - index > 1 else now.year - 1,
                )
                month_end = (
                    datetime(month_start.year, month_start.month % 12 + 1, 1)
                    if month_start.month < 12
                    else datetime(month_start.year + 1, 1, 1)
                )
                records = self._get_sales_records(
                    db, start=month_start, end=month_end
                )
                month_totals.append(sum(float(item.total_amount) for item in records))

            current_total = month_totals[0]
            previous_total = month_totals[1] if len(month_totals) > 1 else 0.0
            trend = "increasing" if current_total >= previous_total else "decreasing"
            response = (
                f"Sales trend is {trend}. This month is "
                f"{self._to_currency(current_total)} and the previous month was "
                f"{self._to_currency(previous_total)}."
            )

            return {
                "intent": "sales_trend",
                "period": "last_six_months",
                "total_amount": float(current_total),
                "response": response,
                "records": len(month_totals),
            }
        finally:
            db.close()

    def _handle_average_sales_query(self, question: str) -> dict:
        db: Session = database_service.create_session()
        try:
            now = datetime.now()
            records = self._get_sales_records(db)
            if not records:
                total = 0.0
                avg = 0.0
            else:
                total = sum(float(item.total_amount) for item in records)
                avg = total / len(records)

            response = (
                f"The average sale value is {self._to_currency(avg)}."
            )

            return {
                "intent": "average_sales",
                "period": "all_time",
                "total_amount": float(avg),
                "response": response,
                "records": len(records),
            }
        finally:
            db.close()
