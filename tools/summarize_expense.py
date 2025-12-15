"""
tools/analytics/summarize_expense.py - Fornece resumo estatístico.
"""
import sqlite3
from typing import Dict
import services.db_connector as db_connector

def summarize_expense(db_file: str, user_id: int) -> Dict:
    """
    Returns a summary of expenses for a given user:
    - total_spent_lifetime
    - transaction_count
    - avg_transaction_value
    """
    sql = """
    SELECT
        COALESCE(SUM(amount), 0) AS total_spent_lifetime,
        COUNT(*) AS transaction_count,
        COALESCE(AVG(amount), 0) AS avg_transaction_value
    FROM expenses
    WHERE user_id = ?
    """

    conn = db_connector.create_connection(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()

        # row = (total, count, avg)
        return {
            "total_spent_lifetime": float(row[0] or 0.0),
            "transaction_count": int(row[1] or 0),
            "avg_transaction_value": float(row[2] or 0.0),
        }

    except sqlite3.Error:
        return {
            "total_spent_lifetime": 0.0,
            "transaction_count": 0,
            "avg_transaction_value": 0.0,
        }
    finally:
        if conn:
            conn.close()
