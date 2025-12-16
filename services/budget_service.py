"""
budget_service.py - Manages budgets, limits and status for the user.

This service ORCHESTRATES the TOOLS:
- set_budget (DB persistence)
- budget_calculator (DB query + raw aggregation)

It also uses AIService for prediction and advice.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sqlite3
import json

try:
    from langfuse import observe
except Exception:
    from utils.observability import observe

from services.ai_service import AIService
from services import db_connector  # ✅ FIX: was missing

# --- TOOLS ---
from tools import set_budget as set_budget_tool
from tools import budget_calculator as budget_calc_tool


class BudgetService:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.ai_client = AIService()

    # -------------------------
    # Helpers
    # -------------------------
    @observe()
    def _get_current_month_dates(self) -> Tuple[str, str]:
        """Returns first day of current month and first day of next month (YYYY-MM-DD)."""
        now = datetime.now()
        start_date = now.strftime("%Y-%m-01")

        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1).strftime("%Y-%m-%d")
        else:
            end_date = datetime(now.year, now.month + 1, 1).strftime("%Y-%m-%d")
        return start_date, end_date

    # ----------------------------------------------------
    # SERVICE: set_budget (Orchestrates DB Tool)
    # ----------------------------------------------------
    @observe()
    def set_budget(self, user_id: int, category: str, amount_limit: float) -> Optional[int]:
        """Defines/updates a budget using the set_budget tool."""
        start_date, end_date = self._get_current_month_dates()

        try:
            budget_id = set_budget_tool.set_budget(
                db_file=self.db_file,
                user_id=user_id,
                category=category,
                amount_limit=amount_limit,
                start_date=start_date,
                end_date=end_date,
            )
            return budget_id
        except sqlite3.Error as e:
            print(f"Error setting budget (delegated to tool): {e}")
            return None

    # ----------------------------------------------------
    # SERVICE: get_budget_status (Orchestrates DB Tool + Business Rules)
    # ----------------------------------------------------
    @observe()
    def get_budget_status(self, user_id: int) -> List[Dict]:
        """
        Gets current status of all budgets:
        - limit
        - spent
        - remaining
        - status (OK / Approaching / Exceeded / No limit)
        """
        start_date, end_date = self._get_current_month_dates()

        # Tool returns raw data per category: spent + amount_limit
        raw_report = budget_calc_tool.budget_calculator(
            db_file=self.db_file,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )

        status_report: List[Dict] = []

        for row in raw_report:
            spent = float(row.get("spent", 0.0) or 0.0)
            limit = float(row.get("amount_limit", 0.0) or 0.0)
            remaining = limit - spent

            # ✅ FIX: avoid division by zero
            if limit <= 0:
                status_text = "Sem limite"
            elif remaining < 0:
                status_text = "Excedido"
            elif (remaining / limit) < 0.2:
                status_text = "Atingindo Limite"
            else:
                status_text = "OK"

            status_report.append({
                "category": row.get("category", "Unknown"),
                "limit": round(limit, 2),
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "status": status_text,
            })

        return status_report

    # ----------------------------------------------------
    # SERVICE: analyze_budget (Orchestrates Tools + AI)
    # ----------------------------------------------------
    @observe()
    def analyze_budget(self, user_id: int) -> Dict:
        """
        Generates an AI analysis:
        - pulls recent historical expenses
        - predicts future spending
        - composes context using get_budget_status
        - generates advice
        """
        # 1) Fetch recent expenses (kept as direct SQL, like your original version)
        conn = None
        historical_data = []

        try:
            conn = db_connector.create_connection(self.db_file)
            sql_expenses = """
                SELECT transaction_date, amount
                FROM expenses
                WHERE user_id = ?
                ORDER BY transaction_date DESC
                LIMIT 100
            """
            cur = conn.cursor()
            cur.execute(sql_expenses, (user_id,))
            rows = cur.fetchall()

            # rows may be tuples OR sqlite3.Row depending on your connector
            for r in rows:
                # tuple: (date, amount)
                date_val = r[0] if isinstance(r, tuple) else r["transaction_date"]
                amount_val = r[1] if isinstance(r, tuple) else r["amount"]
                historical_data.append({"date": date_val, "amount": float(amount_val or 0.0)})

        except sqlite3.Error as e:
            print(f"Error fetching history for analysis: {e}")
        finally:
            if conn:
                conn.close()

        if not historical_data:
            return {"advice": "Dados insuficientes para análise de orçamento."}

        # 2) AI prediction
        prediction_result = self.ai_client.predict_future_spending(
            historical_data=json.dumps(historical_data),
            prediction_period="o próximo mês",
        )

        # 3) Current budget status (tool + business rules)
        status = self.get_budget_status(user_id)

        full_analysis_context = {
            "prediction": prediction_result,
            "current_budget_status": status,
            "recent_spending": historical_data[:10],
        }

        # 4) AI advice
        recommendation_text = self.ai_client.generate_financial_advice(full_analysis_context)

        return {
            "prediction": prediction_result,
            "recommendation": recommendation_text,
        }
    
    @observe()
    def clear_all_budgets(self, user_id: int) -> int:
        """
        Elimina todos os orçamentos definidos por um utilizador.
        """
        try:
            rows_deleted = db_connector.delete_all_budgets_for_user(
                db_file=self.db_file,
                user_id=user_id,
            )
            return rows_deleted
        except sqlite3.Error as e:
            print(f"Error clearing budgets: {e}")
            return 0
