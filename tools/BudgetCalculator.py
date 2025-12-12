"""
tools/budget/budget_calculator.py - Calcula o status de orçamento (limite vs. gasto).
"""
import sqlite3
import db_connector
from typing import List, Dict

def calculate_budget_status(db_file: str, user_id: int, start_date: str, end_date: str) -> List[Dict]:
    """
    TOOL: budget_calculator (get_budget_status). Calcula o gasto real de um período por categoria 
    e compara com os limites definidos na tabela 'budgets'.
    """
    # SQL faz o JOIN entre budgets e expenses para somar os gastos do período
    sql = f"""
    SELECT 
        b.category,
        b.amount_limit,
        COALESCE(SUM(e.amount), 0.0) AS spent
    FROM budgets b
    LEFT JOIN expenses e ON b.user_id = e.user_id AND b.category = e.category
        AND e.transaction_date >= ? AND e.transaction_date < ?
    WHERE b.user_id = ? AND b.start_date = ?
    GROUP BY b.category, b.amount_limit
    """
    
    conn = None
    try:
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()
        
        # Executa a query
        params = (user_id, start_date, end_date, user_id, start_date)
        cursor.execute(sql, params)
        
        # Retorna os resultados brutos (cabe ao Service calcular o 'remaining' e 'status')
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Erro no cálculo do status do orçamento: {e}")
        return []
    finally:
        if conn:
            conn.close()