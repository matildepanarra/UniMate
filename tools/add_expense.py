"""
Tool to add a new expense record to the database.
"""
import sqlite3
from typing import Optional
from services import db_connector
from langfuse import observe 

@observe()
def add_expense(
    db_file: str,
    user_id: int,
    amount: float,
    category: str,
    vendor: str,
    transaction_date: str,
    notes: str = ""
) -> Optional[int]:
    """
    TOOL: add_expense
    Adds a new expense record to the database.

    Args:
        db_file: Path to SQLite DB.
        user_id: Expense owner.
        amount: Expense amount.
        category: Expense category.
        vendor: Vendor/merchant.
        transaction_date: YYYY-MM-DD.
        notes: Optional notes.

    Returns:
        New expense id or None.
    """
    sql = """
    INSERT INTO expenses (user_id, amount, category, vendor, transaction_date, notes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """

    conn = db_connector.create_connection(db_file)
    try:
        cursor = conn.cursor()
        final_notes = notes.strip() if notes else f"Vendor: {vendor}"
        cursor.execute(sql, (user_id, amount, category, vendor, transaction_date, final_notes))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print("Erro add_expense:", e)
        return None
    finally:
        conn.close()
