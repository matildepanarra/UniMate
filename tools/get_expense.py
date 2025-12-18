# tools/expense/get_expense.py
import sqlite3
from typing import Optional, Dict, Any
from services import db_connector
from langfuse import observe 

@observe()
def get_expense(db_file: str, expense_id: int) -> Optional[Dict[str, Any]]:
    """
    TOOL: get_expense
    Fetch one expense by id.

    Args:
        db_file (str): The database file path.
        expense_id (int): The ID of the expense to fetch.   
    
    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the expense if found, otherwise None
    """
    sql = "SELECT * FROM expenses WHERE id = ?"

    conn = db_connector.create_connection(db_file)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, (expense_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Erro ao buscar despesa no DB: {e}")
        return None
    finally:
        conn.close()
