"""
tools/budget/set_budget.py - Define/Atualiza o limite de orçamento.
"""

import sqlite3
from services import db_connector
from typing import Optional
from datetime import datetime
from langfuse import observe 

@observe()
def set_budget(
    db_file: str,
    user_id: int,
    category: str,
    amount_limit: float,
    start_date: str,
    end_date: str
) -> Optional[int]:
    """
    TOOL: set_budget. Atualiza ou insere (upsert) um orçamento.

    Args:
        db_file (str): O caminho do ficheiro de base de dados.
        user_id (int): O ID do utilizador.
        category (str): A categoria do orçamento.
        amount_limit (float): O limite do orçamento.
        start_date (str): A data de início do orçamento (YYYY-MM-DD).
        end_date (str): A data de fim do orçamento (YYYY-MM-DD).
    
    Returns:
        Optional[int]: O ID do orçamento atualizado/inserido, ou None em caso de erro.  
    """
    created_at = datetime.now().isoformat()

    conn = None
    try:
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()

        # 1) Tenta UPDATE
        sql_update = """
        UPDATE budgets
        SET amount_limit = ?, end_date = ?, created_at = ?
        WHERE user_id = ? AND category = ? AND start_date = ?
        """
        cursor.execute(
            sql_update,
            (amount_limit, end_date, created_at, user_id, category, start_date) # <--- REMOVIDO 'end_date' dos WHERE params
        )

        if cursor.rowcount > 0:
            # Buscar o ID do registo atualizado (AQUI TAMBÉM DEVE SER MUDADO)
            cursor.execute(
                """
                SELECT id FROM budgets
                WHERE user_id = ? AND category = ? AND start_date = ? 
                ORDER BY id DESC
                LIMIT 1
                """, # <--- REMOVIDO "AND end_date = ?"
                (user_id, category, start_date) # <--- REMOVIDO 'end_date' dos WHERE params
            )
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None

        # 2) Se não existia, faz INSERT
        sql_insert = """
        INSERT INTO budgets (user_id, category, amount_limit, start_date, end_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(
            sql_insert,
            (user_id, category, amount_limit, start_date, end_date, created_at)
        )
        conn.commit()
        return cursor.lastrowid

    except sqlite3.Error as e:
        print(f"Erro ao atualizar/inserir orçamento: {e}")
        return None
    finally:
        if conn:
            conn.close()

