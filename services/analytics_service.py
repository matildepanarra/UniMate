"""
analytics_service.py - Fornece relatórios e insights de dados agregados usando SQLite.
"""
from typing import List, Dict
import sqlite3
from services import db_connector
from datetime import datetime
from langfuse import observe
from typing import Optional, Tuple

class AnalyticsService:
    def __init__(self, db_file: str):
        self.db_file = db_file

    # --- Funções Auxiliares de DB ---
    @observe()
    def _execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Função utilitária para executar consultas SELECT e retornar resultados como lista de dicionários."""
        conn = None
        try:
            conn = db_connector.get_connection(self.db_file)
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro na consulta SQL: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: get_category_breakdown (Relatório de Distribuição)
    # ----------------------------------------------------
    @observe()
    def get_category_breakdown(self, user_id: int) -> Dict:
        """
        Calcula a despesa total e percentual por categoria, usando GROUP BY.
        """
        sql = """
        SELECT 
            category,
            SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total_spent DESC
        """
        
        category_totals = self._execute_query(sql, (user_id,))
        total_spent_lifetime = sum(item['total_spent'] for item in category_totals)
        
        breakdown = {}
        for item in category_totals:
            total = item['total_spent']
            breakdown[item['category']] = {
                "total": round(total, 2),
                "percentage": round((total / total_spent_lifetime) * 100, 2)
            }
        
        breakdown['total_spent_lifetime'] = round(total_spent_lifetime, 2)
        return breakdown

    # ----------------------------------------------------
    # TOOL: summarize_expense (Resumo Simples)
    # ----------------------------------------------------
    @observe()
    def summarize_expense(self, user_id: int) -> Dict:
        """
        Fornece um resumo de alto nível (total gasto e contagem de transações).
        """
        sql = """
        SELECT 
            SUM(amount) AS total_spent,
            COUNT(id) AS transaction_count,
            AVG(amount) AS avg_transaction_value
        FROM expenses
        WHERE user_id = ?
        """
        summary = self._execute_query(sql, (user_id,))
        
        # O resultado vem como uma lista com um dicionário
        if summary and summary[0]['total_spent'] is not None:
            return {
                "total_spent_lifetime": round(summary[0]['total_spent'], 2),
                "transaction_count": summary[0]['transaction_count'],
                "avg_transaction_value": round(summary[0]['avg_transaction_value'], 2)
            }
        return {
            "total_spent_lifetime": 0.0, 
            "transaction_count": 0, 
            "avg_transaction_value": 0.0
        }

    # ----------------------------------------------------
    # TOOL: get_spending_trends (Análise de Tendências)
    # ----------------------------------------------------
    @observe()
    def get_spending_trends(self, user_id: int) -> Dict:
        """
        Agrega gastos por mês/ano para identificar tendências.
        """
        sql = """
        SELECT
            strftime('%Y-%m', transaction_date) as year_month,
            SUM(amount) AS total_spent
        FROM expenses
        WHERE user_id = ?
        GROUP BY year_month
        ORDER BY year_month ASC
        """
        trends_data = self._execute_query(sql, (user_id,))
        
        # Formatar para um dicionário de tendências
        trends = {item['year_month']: round(item['total_spent'], 2) for item in trends_data}
        return {"period": "monthly", "data": trends}

    # ----------------------------------------------------
    # TOOL: detect_anomalies (Deteção de Anomalias Simples no DB)
    # ----------------------------------------------------
    @observe()
    def detect_anomalies(self, user_id: int) -> List[Dict]:
        """
        Identifica despesas que são significativamente maiores que a média.
        Usamos uma subconsulta para calcular a média de gastos do usuário.
        """
        sql = """
        SELECT
            id, amount, vendor, transaction_date
        FROM expenses
        WHERE user_id = ? AND amount > (
            SELECT AVG(amount) * 2.0  -- Condição: Montante > 2 vezes a média
            FROM expenses
            WHERE user_id = ? AND amount > 0 
        )
        """
        anomalies = self._execute_query(sql, (user_id, user_id))
        
        return [
            {
                "expense_id": a['id'], 
                "amount": a['amount'], 
                "description": a['vendor'], 
                "reason": "Valor excede 200% do valor médio de transação."
            }
            for a in anomalies
        ]