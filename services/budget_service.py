"""
budget_service.py - Manages budgets, limits and user status using SQLite.
Depends on ExpenseService for spending data.
"""
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
try:
    from langfuse import observe  
except Exception:
    from utils.observability import observe
from services import db_connector 
from services.ai_service import AIService 
from typing import Optional, Tuple
import json

# --- Budget Service ---
class BudgetService:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.ai_client = AIService()

    # --- Auxiliary DB Functions ---
    @observe()
    def _get_current_month_dates(self) -> Tuple[str, str]:
        """Returns the first and last day of the current month (YYYY-MM-DD)."""
        now = datetime.now()
        start_date = now.strftime("%Y-%m-01")

        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1).strftime("%Y-%m-%d")
        else:
            end_date = datetime(now.year, now.month + 1, 1).strftime("%Y-%m-%d")
        return start_date, end_date
    
    # ----------------------------------------------------
    # TOOL: set_budget (Persistency in the DB)
    # ----------------------------------------------------
    @observe()
    def set_budget(self, user_id: int, category: str, amount_limit: float) -> Optional[int]:
        """
        Define or update a budget limit (assumed to be monthly) in the 'budgets' table.
        """
        start_date, end_date = self._get_current_month_dates()
        created_at = datetime.now().isoformat()
        
        conn = None
        try:
            conn = db_connector.get_connection(self.db_file)
            cursor = conn.cursor()
            
            sql_update = """
            UPDATE budgets SET amount_limit = ?, created_at = ?
            WHERE user_id = ? AND category = ? AND start_date = ?
            """
            cursor.execute(sql_update, (amount_limit, created_at, user_id, category, start_date))
            
            if cursor.rowcount == 0:
                sql_insert = """
                INSERT INTO budgets (user_id, category, amount_limit, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (user_id, category, amount_limit, start_date, end_date, created_at))
            
            conn.commit()
            print(f"Budget to {category} defined/updated for R$ {amount_limit}.")
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error defining budget in DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: budget_calculator -> get_budget_status (Consults in the DB)
    # ----------------------------------------------------
    @observe()
    def get_budget_status(self, user_id: int) -> List[Dict]:
        """
        Calculates the current status of all budgets (Limit vs. Actual Spending).
        This uses a subquery SQL to calculate the spending per category.
        """
        start_date, end_date = self._get_current_month_dates()

        sql = f"""
        SELECT 
            b.category,
            b.amount_limit,
            -- Subconsulta para calcular o total gasto neste mês
            COALESCE(SUM(e.amount), 0.0) AS spent
        FROM budgets b
        LEFT JOIN expenses e ON b.user_id = e.user_id AND b.category = e.category
            AND e.transaction_date >= '{start_date}' AND e.transaction_date < '{end_date}'
        WHERE b.user_id = ? AND b.start_date = '{start_date}'
        GROUP BY b.category, b.amount_limit
        """
        conn = None
        status_report = []
        try:
            conn = db_connector.get_connection(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            
            for row in cursor.fetchall():
                spent = row['spent']
                limit = row['amount_limit']
                remaining = limit - spent
                
                status_report.append({
                    "category": row['category'],
                    "limit": limit,
                    "spent": round(spent, 2),
                    "remaining": round(remaining, 2),
                    "status": "Exceeded" if remaining < 0 else ("Approaching Limit" if remaining / limit < 0.2 else "OK")
                })
            return status_report
        except sqlite3.Error as e:
            print(f"Error getting budget status: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: budget_calculator -> analyze_budget (AI Analysis)
    # ----------------------------------------------------
    @observe()
    def analyze_budget(self, user_id: int) -> Dict:
        """
        Orchestrates the budget analysis, getting data and calling the AI prediction.
        """
        # (The logic of fetching data for the AI and calling predict_future_spending
        #  from AIService remains the same from the previous draft, adapted for DB)
        
        # 1. Retrieve spending data (Simply retrieve all expenses for the AI)
        conn = None
        historical_data = []
        try:
            conn = db_connector.get_connection(self.db_file)
            sql_expenses = "SELECT transaction_date, amount FROM expenses WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 100"
            cursor = conn.cursor()
            cursor.execute(sql_expenses, (user_id,))
            
            historical_data = [{'date': row['transaction_date'], 'amount': row['amount']} for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error fetching historical data for analysis: {e}")
        finally:
            if conn:
                conn.close()
        
        if not historical_data:
            return {"advice": "Insufficient data for budget analysis."}
        
        historical_data_json = json.dumps(historical_data)
        
        # 2. Call to AIService (AI_SERVICE: predict_future_spending)
        prediction_result = self.ai_client.predict_future_spending(
            historical_data=historical_data_json,
            prediction_period="the next month"
        )

        # 3. Generates advice (the AIService does the final reasoning)
        status = self.get_budget_status(user_id)
        
        full_analysis_context = {
            "prediction": prediction_result,
            "current_budget_status": status,
            "recent_spending": historical_data[:10]
        }

        # Call the AIService to generate final advice (TOOL: generate_financial_advice)
        recommendation_text = self.ai_client.generate_financial_advice(full_analysis_context)

        return {
            "prediction": prediction_result,
            "recommendation": recommendation_text
        }