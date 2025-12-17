# tools/list_expenses.py
from typing import List, Dict, Optional
import sqlite3

def list_expenses(
    db_file: str,
    user_id: int,
    limit: int = 200,
    offset: int = 0,
    category: Optional[str] = None,
    start_date: Optional[str] = None,  # YYYY-MM-DD
    end_date: Optional[str] = None,    # YYYY-MM-DD (exclusive or inclusive—here inclusive)
) -> List[Dict]:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
    SELECT id, user_id, amount, category, vendor, transaction_date, notes
    FROM expenses
    WHERE user_id = ?
    """
    params = [int(user_id)]

    if category:
        sql += " AND category = ?"
        params.append(category)

    if start_date:
        sql += " AND transaction_date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND transaction_date <= ?"
        params.append(end_date)

    sql += " ORDER BY transaction_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]
