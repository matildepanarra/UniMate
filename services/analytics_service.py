#"""
#analytics_service.py - Gives reports and insights of aggregated data using SQLite.
#"""
#from typing import List, Dict
#import sqlite3
#from services import db_connector
#from datetime import datetime
#try:
#    from langfuse import observe  
#except Exception:
#    from utils.observability import observe
#from typing import Optional, Tuple
#
#class AnalyticsService:
#    def __init__(self, db_file: str):
#        self.db_file = db_file
#
#    # ---Auxiliary DB Functions---
#    @observe()
#    def _execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
#        """Function used to execute SELECT queries and return results as a list of #dictionaries."""
#        conn = None
#        try:
#            conn = db_connector.get_connection(self.db_file)
#            conn.row_factory = sqlite3.Row
#            cursor = conn.cursor()
#            cursor.execute(sql, params or ())
#            return [dict(row) for row in cursor.fetchall()]
#        except sqlite3.Error as e:
#            print(f"Error in the SQL query: {e}")
#            return []
#        finally:
#            if conn:
#                conn.close()
#
#    # ----------------------------------------------------
#    # TOOL: get_category_breakdown (Distribution Report)
#    # ----------------------------------------------------
#    @observe()
#    def get_category_breakdown(self, user_id: int) -> Dict:
#        """
#        Calculates the total and percentage spent per category, using GROUP BY.
#        """
#        sql = """
#        SELECT 
#            category,
#            SUM(amount) AS total_spent
#        FROM expenses
#        WHERE user_id = ?
#        GROUP BY category
#        ORDER BY total_spent DESC
#        """
#        
#        category_totals = self._execute_query(sql, (user_id,))
#        total_spent_lifetime = sum(item['total_spent'] for item in category_totals)
#        
#        breakdown = {}
#        for item in category_totals:
#            total = item['total_spent']
#            breakdown[item['category']] = {
#                "total": round(total, 2),
#                "percentage": round((total / total_spent_lifetime) * 100, 2)
#            }
#        
#        breakdown['total_spent_lifetime'] = round(total_spent_lifetime, 2)
#        return breakdown
#
#    # ----------------------------------------------------
#    # TOOL: summarize_expense (Simple Summary)
#    # ----------------------------------------------------
#    @observe()
#    def summarize_expense(self, user_id: int) -> Dict:
#        """
#        Provides a high-level summary (total spent and transaction count).
#        """
#        sql = """
#        SELECT 
#            SUM(amount) AS total_spent,
#            COUNT(id) AS transaction_count,
#            AVG(amount) AS avg_transaction_value
#        FROM expenses
#        WHERE user_id = ?
#        """
#        summary = self._execute_query(sql, (user_id,))
#        
#        if summary and summary[0]['total_spent'] is not None:
#            return {
#                "total_spent_lifetime": round(summary[0]['total_spent'], 2),
#                "transaction_count": summary[0]['transaction_count'],
#                "avg_transaction_value": round(summary[0]['avg_transaction_value'], 2)
#            }
#        return {
#            "total_spent_lifetime": 0.0, 
#            "transaction_count": 0, 
#            "avg_transaction_value": 0.0
#        }
#
#    # ----------------------------------------------------
#    # TOOL: get_spending_trends (Trend Analysis)
#    # ----------------------------------------------------
#    @observe()
#    def get_spending_trends(self, user_id: int) -> Dict:
#        """
#        Aggregates expenses by month/year to identify trends.
#        """
#        sql = """
#        SELECT
#            strftime('%Y-%m', transaction_date) as year_month,
#            SUM(amount) AS total_spent
#        FROM expenses
#        WHERE user_id = ?
#        GROUP BY year_month
#        ORDER BY year_month ASC
#        """
#        trends_data = self._execute_query(sql, (user_id,))
#        
#        trends = {item['year_month']: round(item['total_spent'], 2) for item in trends_data}
#        return {"period": "monthly", "data": trends}
#
#    # ----------------------------------------------------
#    # TOOL: detect_anomalies (Simple Anomaly Detection in DB)
#    # ----------------------------------------------------
#    @observe()
#    def detect_anomalies(self, user_id: int) -> List[Dict]:
#        """
#        Identifies expenses that are significantly larger than the average.
#        We use a subquery to calculate the average spending of the user.
#        """
#        sql = """
#        SELECT
#            id, amount, vendor, transaction_date
#        FROM expenses
#        WHERE user_id = ? AND amount > (
#            SELECT AVG(amount) * 2.0  -- Condition: Amount > 2 times the average
#            FROM expenses
#            WHERE user_id = ? AND amount > 0 
#        )
#        """
#        anomalies = self._execute_query(sql, (user_id, user_id))
#        
#        return [
#            {
#                "expense_id": a['id'], 
#                "amount": a['amount'], 
#                "description": a['vendor'], 
#                "reason": "Value exceeds 200% of the average transaction value."
#            }
#            for a in anomalies
#        ]




"""
analytics_service.py - Gives reports and insights of aggregated data using SQLite.

ORCHESTRATES the TOOLS:
- detect_anomalies
- get_spending_trend
"""
from typing import List, Dict, Optional, Tuple
import sqlite3
from services import db_connector # Necessário para a lógica interna dos métodos remanescentes
from datetime import datetime
try:
    from langfuse import observe  
except Exception:
    from utils.observability import observe
from typing import Optional, Tuple

# --- IMPORTAÇÃO DAS TOOLS DE TERCEIROS ---
from tools.detect_anomalies import detect_anomalies as detect_anomalies_tool
from tools.get_spending_trend import get_spending_trend as get_spending_trend_tool


class AnalyticsService:
    def __init__(self, db_file: str):
        self.db_file = db_file

    # ---Auxiliary DB Functions (MANTIDA para métodos sem Tool)---
    @observe()
    def _execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Função usada para executar consultas SELECT e retornar resultados."""
        conn = None
        try:
            conn = db_connector.get_connection(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error in the SQL query: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # SERVICE: get_category_breakdown (Distribution Report) - Lógica de Agregação no Serviço
    # ----------------------------------------------------
    @observe()
    def get_category_breakdown(self, user_id: int) -> Dict:
        """
        Calculates the total and percentage spent per category, using GROUP BY.
        """
        sql = """
        SELECT 
            category,
            SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total_spent DESC
        """
        
        category_totals = self._execute_query(sql, (user_id,))
        total_spent_lifetime = sum(item['total_spent'] for item in category_totals)
        
        breakdown = {}
        for item in category_totals:
            total = item['total_spent']
            # Evita divisão por zero
            percentage = (total / total_spent_lifetime) * 100 if total_spent_lifetime else 0
            
            breakdown[item['category']] = {
                "total": round(total, 2),
                "percentage": round(percentage, 2)
            }
        
        breakdown['total_spent_lifetime'] = round(total_spent_lifetime, 2)
        return breakdown

    # ----------------------------------------------------
    # SERVICE: summarize_expense (Simple Summary) - Lógica de Agregação no Serviço
    # ----------------------------------------------------
    @observe()
    def summarize_expense(self, user_id: int) -> Dict:
        """
        Provides a high-level summary (total spent and transaction count).
        """
        sql = """
        SELECT 
            SUM(amount) AS total_spent,
            COUNT(id) AS transaction_count,
            AVG(amount) AS avg_transaction_value
        FROM expenses
        WHERE user_id = ?
        """
        summary = self._execute_query(sql, (user_id,))
        
        if summary and summary[0]['total_spent'] is not None:
            return {
                "total_spent_lifetime": round(summary[0]['total_spent'], 2),
                "transaction_count": summary[0]['transaction_count'],
                "avg_transaction_value": round(summary[0]['avg_transaction_value'] or 0.0, 2)
            }
        return {
            "total_spent_lifetime": 0.0, 
            "transaction_count": 0, 
            "avg_transaction_value": 0.0
        }

    # ----------------------------------------------------
    # SERVICE: get_spending_trends (Chama a Tool)
    # ----------------------------------------------------
    @observe()
    def get_spending_trends(self, user_id: int) -> Dict:
        """
        Aggregates expenses by month/year to identify trends by calling the Tool.
        """
        # A Tool retorna uma Lista de Dicts: [{"year_month": "2023-10", "total_spent": 120.0}]
        trends_data = get_spending_trend_tool(self.db_file, user_id)
        
        # O Serviço transforma o formato de saída da Tool para o formato original esperado
        trends = {item['year_month']: round(item['total_spent'], 2) for item in trends_data}
        return {"period": "monthly", "data": trends}

    # ----------------------------------------------------
    # SERVICE: detect_anomalies (Chama a Tool)
    # ----------------------------------------------------
    @observe()
    def detect_anomalies(self, user_id: int) -> List[Dict]:
        """
        Identifies expenses that are significantly larger than the average by calling the Tool.
        """
        # A Tool retorna os campos brutos: id, amount, vendor, transaction_date
        anomalies_raw = detect_anomalies_tool(self.db_file, user_id)
        
        # O Serviço formata o output da Tool para o formato final esperado
        return [
            {
                "expense_id": a['id'], 
                "amount": a['amount'], 
                "description": a['vendor'], 
                "reason": "Value exceeds 200% of the average transaction value."
            }
            for a in anomalies_raw
        ]