"""
Tool to list expenses with optional filters.
"""
from typing import List, Dict, Optional
import sqlite3
from langfuse import observe 

@observe()
def list_expenses(
    db_file: str,
    user_id: int,
    limit: int = 200,
    offset: int = 0,
    category: Optional[str] = None,
    start_date: Optional[str] = None,  # YYYY-MM-DD
    end_date: Optional[str] = None,    # YYYY-MM-DD (exclusive or inclusive—here inclusive)
) -> List[Dict]:
    """
    TOOL: list_expenses
    Lista despesas com filtros opcionais.
    
    Args:
        db_file (str): O caminho do ficheiro de base de dados.
        user_id (int): O ID do utilizador.
        limit (int, optional): Número máximo de despesas a retornar. Padrão é 200.
        offset (int, optional): Número de despesas a pular para paginação. Padrão é 0.
        category (Optional[str], optional): Filtra por categoria específica. Padrão é None.
        start_date (Optional[str], optional): Filtra despesas a partir desta data (YYYY-MM-DD). Padrão é None.
        end_date (Optional[str], optional): Filtra despesas até esta data (YYYY-MM-DD). Padrão é None.
    
    Returns:
        List[Dict]: Uma lista de dicionários representando as despesas.
    """
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
