"""
tools/expense/get_expense.py - Busca uma despesa na tabela 'expenses'.
"""
import sqlite3
from services import db_connector
from typing import Optional, Dict

def get_expense(db_file: str, expense_id: int) -> Optional[Dict]:
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