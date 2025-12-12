"""
budget_service.py - Gerencia orçamentos, limites e status do usuário usando SQLite.
Depende do ExpenseService para dados de gastos.
"""
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
# Assumimos que o seu módulo de base de dados é 'db_connector'
import db_connector 
from ai_service import AIService 

# --- SERVIÇO DE ORÇAMENTO ---
class BudgetService:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.ai_client = AIService()

    # --- Funções Auxiliares de DB ---

    def _get_current_month_dates(self) -> Tuple[str, str]:
        """Retorna o primeiro e o último dia do mês atual (YYYY-MM-DD)."""
        now = datetime.now()
        start_date = now.strftime("%Y-%m-01")
        # Para simplificar, o end_date é o último dia do mês, ou pode ser 2999-12-31 se for orçamento permanente.
        # Aqui, usamos o primeiro dia do próximo mês para garantir que a consulta SQL funciona.
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1).strftime("%Y-%m-%d")
        else:
            end_date = datetime(now.year, now.month + 1, 1).strftime("%Y-%m-%d")
        return start_date, end_date
    
    # ----------------------------------------------------
    # TOOL: set_budget (Persistência no DB)
    # ----------------------------------------------------
    def set_budget(self, user_id: int, category: str, amount_limit: float) -> Optional[int]:
        """
        Define ou atualiza um limite de orçamento (assumido ser mensal) na tabela 'budgets'.
        """
        start_date, end_date = self._get_current_month_dates()
        created_at = datetime.now().isoformat()
        
        conn = None
        try:
            conn = db_connector.create_connection(self.db_file)
            cursor = conn.cursor()
            
            # Tenta atualizar primeiro (se já existir para a categoria neste mês)
            sql_update = """
            UPDATE budgets SET amount_limit = ?, created_at = ?
            WHERE user_id = ? AND category = ? AND start_date = ?
            """
            cursor.execute(sql_update, (amount_limit, created_at, user_id, category, start_date))
            
            if cursor.rowcount == 0:
                # Se não atualizou, insere um novo
                sql_insert = """
                INSERT INTO budgets (user_id, category, amount_limit, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_insert, (user_id, category, amount_limit, start_date, end_date, created_at))
            
            conn.commit()
            print(f"Orçamento para {category} definido/atualizado para R$ {amount_limit}.")
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao definir orçamento no DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: budget_calculator -> get_budget_status (Consulta no DB)
    # ----------------------------------------------------
    def get_budget_status(self, user_id: int) -> List[Dict]:
        """
        Calcula o status atual de todos os orçamentos (Limite vs. Gasto Real).
        Isto usa uma subconsulta SQL para calcular o gasto por categoria.
        """
        start_date, end_date = self._get_current_month_dates()

        sql = f"""
        SELECT 
            b.category,
            b.amount_limit,
            -- Subconsulta para calcular o total gasto neste mês
            COALESCE(SUM(e.amount), 0.0) AS spent
        FROM budgets b
        LEFT JOIN expenses e ON b.user_id = e.user_id AND b.category = e.category
            AND e.transaction_date >= '{start_date}' AND e.transaction_date < '{end_date}'
        WHERE b.user_id = ? AND b.start_date = '{start_date}'
        GROUP BY b.category, b.amount_limit
        """
        conn = None
        status_report = []
        try:
            conn = db_connector.create_connection(self.db_file)
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            
            for row in cursor.fetchall():
                spent = row['spent']
                limit = row['amount_limit']
                remaining = limit - spent
                
                status_report.append({
                    "category": row['category'],
                    "limit": limit,
                    "spent": round(spent, 2),
                    "remaining": round(remaining, 2),
                    "status": "Excedido" if remaining < 0 else ("Atingindo Limite" if remaining / limit < 0.2 else "OK")
                })
            return status_report
        except sqlite3.Error as e:
            print(f"Erro ao obter status do orçamento: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: budget_calculator -> analyze_budget (Análise de IA)
    # ----------------------------------------------------
    def analyze_budget(self, user_id: int) -> Dict:
        """
        Orquestra a análise do orçamento, obtendo dados e chamando a previsão da IA.
        """
        # (A lógica de obter os dados para a IA e chamar o predict_future_spending
        #  do AIService permanece a mesma do rascunho anterior, adaptada para DB)
        
        # 1. Recuperar dados de gastos (Simplesmente recuperamos todas as despesas para a IA)
        conn = None
        historical_data = []
        try:
            conn = db_connector.create_connection(self.db_file)
            sql_expenses = "SELECT transaction_date, amount FROM expenses WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 100"
            cursor = conn.cursor()
            cursor.execute(sql_expenses, (user_id,))
            
            historical_data = [{'date': row['transaction_date'], 'amount': row['amount']} for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Erro ao buscar histórico para análise: {e}")
        finally:
            if conn:
                conn.close()
        
        if not historical_data:
            return {"advice": "Dados insuficientes para análise de orçamento."}
        
        historical_data_json = json.dumps(historical_data)
        
        # 2. Chamada ao AIService (AI_SERVICE: predict_future_spending)
        prediction_result = self.ai_client.predict_future_spending(
            historical_data=historical_data_json,
            prediction_period="o próximo mês"
        )
        
        # 3. Gerar conselho (o AIService faz o raciocínio final)
        status = self.get_budget_status(user_id)
        
        # Combinamos todos os dados para a IA
        full_analysis_context = {
            "prediction": prediction_result,
            "current_budget_status": status,
            "recent_spending": historical_data[:10]
        }
        
        # Chamada ao AIService para gerar conselho final (TOOL: generate_financial_advice)
        recommendation_text = self.ai_client.generate_financial_advice(full_analysis_context)

        return {
            "prediction": prediction_result,
            "recommendation": recommendation_text
        }