"""
tools/analytics/detect_anomalies.py - Identifica gastos anómalos.
"""
from typing import Dict, List
from services import db_connector
from langfuse import observe 

@observe()
def detect_anomalies(db_file: str, user_id: int) -> List[Dict]:
    """
    TOOL: detect_anomalies
    Identifica despesas significativamente maiores que a média (2x).

    Args:
        db_file (str): O caminho do ficheiro de base de dados.
        user_id (int): O ID do utilizador.  

    Returns:
        List[Dict]: Uma lista de dicionários representando despesas anómalas.
    """
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
    return db_connector.execute_select_query(db_file, sql, (user_id, user_id))
