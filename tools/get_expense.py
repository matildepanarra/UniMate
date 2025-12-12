"""
tools/expense/get_expense.py - Busca uma despesa na tabela 'expenses'.
"""
import sqlite3
import db_connector
from typing import Optional, Dict

def select_expense_by_id(db_file: str, expense_id: int) -> Optional[Dict]:
    """
    TOOL: get_expense. Busca uma despesa específica pelo ID.
    """
    sql = "SELECT * FROM expenses WHERE id = ?"
    conn = None
    try:
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()
        cursor.execute(sql, (expense_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row) 
        return None
    except sqlite3.Error as e:
        print(f"Erro ao buscar despesa no DB: {e}")
        return None
    finally:
        if conn:
            conn.close()