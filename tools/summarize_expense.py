"""
tools/analytics/summarize_expense.py - Fornece resumo estatístico.
"""
import sqlite3
import db_connector
from typing import Dict

def get_expense_summary(db_file: str, user_id: int) -> Dict:
    """
    TOOL: summarize_expense. Fornece um resumo de alto nível (total gasto, contagem, média).
    """
    sql = """
    SELECT 
        SUM(amount) AS total_spent,
        COUNT(id) AS transaction_count,
        AVG(amount) AS avg_transaction_value
    FROM expenses
    WHERE user_id = ?
    """
    # Apenas um resultado (fetchone)
    result = db_connector.execute_select_query(db_file, sql, (user_id,))
    
    if result and result[0]['total_spent'] is not None:
        return result[0]
    return {'total_spent': 0.0, 'transaction_count': 0, 'avg_transaction_value': 0.0}