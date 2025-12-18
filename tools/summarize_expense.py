"""
tools/analytics/summarize_expense.py - Fornece resumo estatístico.
"""
import sqlite3
from typing import Dict
import services.db_connector as db_connector
from langfuse import observe 

@observe()
def summarize_expense(db_file: str, user_id: int) -> Dict:
    """
    TOOL: summarize_expense
    Fornece um resumo estatístico das despesas do utilizador.   

    Args:
        db_file (str): O caminho do ficheiro de base de dados.
        user_id (int): O ID do utilizador.
    
    Returns:
        Dict: Um dicionário com total gasto, contagem de transações e valor médio por transação.
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
