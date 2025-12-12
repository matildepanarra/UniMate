"""
tools/budget/set_budget.py - Define/Atualiza o limite de orçamento.
"""
import sqlite3
import db_connector
from typing import Optional

def upsert_budget_limit(db_file: str, user_id: int, category: str, amount_limit: float, 
                        start_date: str, end_date: str) -> Optional[int]:
    """
    TOOL: set_budget. Atualiza ou insere (upsert) um orçamento.
    
    Args: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD).
    """
    created_at = datetime.now().isoformat()
    
    conn = None
    try:
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()
        
        # 1. Tenta Atualizar
        sql_update = """
        UPDATE budgets SET amount_limit = ?, created_at = ?
        WHERE user_id = ? AND category = ? AND start_date = ?
        """
        cursor.execute(sql_update, (amount_limit, created_at, user_id, category, start_date))
        
        if cursor.rowcount == 0:
            # 2. Se não atualizou (rowcount == 0), insere um novo
            sql_insert = """
            INSERT INTO budgets (user_id, category, amount_limit, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_insert, (user_id, category, amount_limit, start_date, end_date, created_at))
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Erro ao atualizar/inserir orçamento: {e}")
        return None
    finally:
        if conn:
            conn.close()