"""
tools/budget/budget_calculator.py - Calcula o status de orçamento (limite vs. gasto).
"""
import sqlite3
from services import db_connector
from typing import List, Dict

def budget_calculator(db_file: str, user_id: int, start_date: str, end_date: str) -> List[Dict]:
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
    LEFT JOIN expenses e ON 
        -- 1. Ligar User (Correto)
        b.user_id = e.user_id 
        -- 2. Ligar Categoria (Correto)
        AND b.category = e.category
        -- 3. CRÍTICO: Ligar a despesa (e) ao PERÍODO DO ORÇAMENTO (b)
        AND e.transaction_date >= b.start_date 
        AND e.transaction_date < b.end_date
    WHERE 
        -- 4. Filtrar o Orçamento ATIVO (do mês atual, que é o start_date passado)
        b.user_id = ? AND b.start_date = ?
    GROUP BY b.category, b.amount_limit, b.start_date
    """
    
    conn = None
    try:
        conn = db_connector.create_connection(db_file)
        cursor = conn.cursor()
        
        # Executa a query
        params = (user_id, start_date) 
        cursor.execute(sql, params)
        
        # Retorna os resultados brutos (cabe ao Service calcular o 'remaining' e 'status')
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Erro no cálculo do status do orçamento: {e}")
        return []
    finally:
        if conn:
            conn.close()