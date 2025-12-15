"""
tools/analytics/get_spending_trends.py - Calcula o gasto agregado mensal.
"""
from typing import Dict, List
from services import db_connector


def get_spending_trend(db_file: str, user_id: int) -> List[Dict]:
    """
    TOOL: get_spending_trends
    Agrega gastos por mês/ano.
    """
    sql = """
    SELECT
        strftime('%Y-%m', transaction_date) as year_month,
        SUM(amount) AS total_spent
    FROM expenses
    WHERE user_id = ?
    GROUP BY year_month
    ORDER BY year_month ASC
    """
    return db_connector.execute_select_query(db_file, sql, (user_id,))