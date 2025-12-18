"""
remove_expense.py
Deletes an expense from the expenses table.
"""

import sqlite3
from typing import Dict
from langfuse import observe 

@observe()
def remove_expense(db_file: str, user_id: int, expense_id: int) -> Dict:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (expense_id, user_id)
    )

    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()

    if rows_deleted == 0:
        return {
            "status": "not_found",
            "message": "Expense not found or does not belong to this user."
        }

    return {
        "status": "success",
        "expense_id": expense_id,
        "message": "Expense removed successfully."
    }
