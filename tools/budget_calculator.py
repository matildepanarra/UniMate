# tools/budget/budget_calculator.py
import sqlite3
from services import db_connector
from typing import List, Dict, Any

def budget_calculator(db_file: str, user_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    TOOL: budget_calculator
    Calculates spent per category for an active budget period and compares with budgets table.
    """
    sql = """
    SELECT 
        b.category,
        b.amount_limit,
        COALESCE(SUM(e.amount), 0.0) AS spent
    FROM budgets b
    LEFT JOIN expenses e ON 
        b.user_id = e.user_id
        AND b.category = e.category
        AND e.transaction_date >= b.start_date 
        AND e.transaction_date < b.end_date
    WHERE 
        b.user_id = ? AND b.start_date = ?
    GROUP BY b.category, b.amount_limit, b.start_date
    """

    conn = db_connector.create_connection(db_file)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, start_date))
        return [dict(r) for r in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Erro no cálculo do status do orçamento: {e}")
        return []
    finally:
        conn.close()
