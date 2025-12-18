"""
analytics_service.py - Gives reports and insights of aggregated data using SQLite.
"""

from typing import Dict, List
from tools.detect_anomalies import detect_anomalies as detect_anomalies_tool
from tools.get_spending_trend import get_spending_trend as get_spending_trend_tool
from services import db_connector

from langfuse import observe



class AnalyticsService:
    def __init__(self, db_file: str):
        self.db_file = db_file

    @observe()
    def detect_anomalies(self, user_id: int) -> List[Dict]:
        rows = detect_anomalies_tool(self.db_file, user_id)
        return [
            {
                "expense_id": r["id"],
                "amount": r["amount"],
                "description": r.get("vendor"),
                "transaction_date": r.get("transaction_date"),
                "reason": "Value exceeds 200% of the average transaction value."
            }
            for r in rows
        ]

    @observe()
    def get_spending_trends(self, user_id: int) -> Dict:
        rows = get_spending_trend_tool(self.db_file, user_id)
        trends = {r["year_month"]: round(r["total_spent"], 2) for r in rows}
        return {"period": "monthly", "data": trends}

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
        
        category_totals = db_connector.execute_select_query(self.db_file, sql, (user_id,))
        total_spent_lifetime = sum(item['total_spent'] for item in category_totals)
        
        breakdown = {}
        for item in category_totals:
            total = item['total_spent']
            breakdown[item['category']] = {
                "total": round(total, 2),
                "percentage": round((total / total_spent_lifetime) * 100, 2)
            }
        
        breakdown['total_spent_lifetime'] = round(total_spent_lifetime, 2)
        return breakdown