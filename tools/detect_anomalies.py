"""
tools/analytics/detect_anomalies.py - Identifica gastos anómalos.
"""
import sqlite3
import db_connector
from typing import List, Dict

def find_spending_anomalies(db_file: str, user_id: int) -> List[Dict]:
    """
    TOOL: detect_anomalies. Identifica despesas que são significativamente maiores que a média (2x).
    """
    # Subconsulta para calcular a média e encontrar valores que a excedem 200%
    sql = """
    SELECT
        id, amount, vendor, transaction_date
    FROM expenses
    WHERE user_id = ? AND amount > (
        SELECT AVG(amount) * 2.0
        FROM expenses
        WHERE user_id = ? AND amount > 0 
    )
    """
    # Os dois parâmetros (user_id) são necessários para a WHERE e a Subquery
    return db_connector.execute_select_query(db_file, sql, (user_id, user_id)) # Assume-se uma função utilitária de SELECT