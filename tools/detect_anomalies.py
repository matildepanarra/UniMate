"""
tools/analytics/detect_anomalies.py - Identifica gastos anómalos.
"""
from typing import Dict, List
from services import db_connector


def detect_anomalies(db_file: str, user_id: int) -> List[Dict]:
    """
    TOOL: detect_anomalies
    Identifica despesas significativamente maiores que a média (2x).
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
