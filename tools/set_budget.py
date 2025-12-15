import sqlite3
from typing import Optional
from datetime import datetime

from services import db_connector


def set_budget(
    db_file: str,
    user_id: int,
    category: str,
    amount_limit: float,
    start_date: str,
    end_date: str,
) -> Optional[int]:
    """
    Inserts or updates a budget for a given user/category/month.
    """

    sql = """
    INSERT INTO budgets (user_id, category, amount_limit, start_date, end_date, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, category, start_date, end_date)
    DO UPDATE SET amount_limit = excluded.amount_limit
    """

    conn = None
    try:
        # ✅ usar SEMPRE o mesmo helper do projeto
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()

        cursor.execute(
            sql,
            (
                user_id,
                category,
                amount_limit,
                start_date,
                end_date,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        return cursor.lastrowid

    except sqlite3.Error as e:
        print(f"[set_budget TOOL ERROR]: {e}")
        return None

    finally:
        if conn:
            conn.close()
