"""
expense_service.py - Gerencia o registro e consulta de despesas do usuário usando SQLite.
Orquestra chamadas ao AIService para extração e categorização.
"""
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
# Assumimos que o seu módulo de base de dados está disponível como 'db_connector'
# Caso o seu arquivo se chame 'database_setup.py', substitua 'db_connector'
import db_connector 
from services import *
from ai_service import AIService 

# --- 1. MODELO DE DADOS DE DESPESA (Mantido, mas ajustado para DB) ---
# Usaremos uma tupla ou dicionário simples para interagir com o DB, 
# mas a classe ajuda na estruturação.
class Expense:
    # A estrutura da classe reflete a tabela 'expenses'
    def __init__(self, user_id: int, amount: float, category: str, vendor: str, 
                 transaction_date: str, notes: Optional[str] = None, expense_id: Optional[int] = None):
        self.expense_id = expense_id
        self.user_id = user_id
        self.amount = amount
        self.category = category
        self.vendor = vendor
        self.transaction_date = transaction_date # YYYY-MM-DD
        self.notes = notes
        self.created_at = datetime.now().isoformat()

    def to_tuple(self):
        # Usado para INSERT na tabela expenses
        return (
            self.user_id,
            self.amount,
            self.category,
            self.vendor,
            self.transaction_date,
            self.notes,
            self.created_at
        )

# --- 2. SERVIÇO DE DESPESAS ---
class ExpenseService:
    """
    Implementa a lógica de negócio para manipulação de despesas, usando SQLite.
    """
    def __init__(self, db_file: str):
        # A conexão será estabelecida a cada chamada para ser thread-safe (prática SQLite)
        self.db_file = db_file 
        self.ai_client = AIService() 
        self.valid_categories = ["Mercearia", "Transporte", "Restaurante", "Lazer", "Casa", "Outros"]

    # ----------------------------------------------------
    # TOOL: add_expense (Persistência no DB)
    # ----------------------------------------------------
    def add_expense(self, user_id: int, amount: float, description: str, date_str: str, category: str) -> Optional[int]:
        """
        Insere uma nova despesa na tabela 'expenses'.
        """
        sql = """
        INSERT INTO expenses (user_id, amount, category, vendor, transaction_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        # O campo 'vendor' no DB corresponde à 'description' na nossa lógica
        new_expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            vendor=description,
            transaction_date=date_str,
            notes=f"Categoria classificada por IA: {category}" # Exemplo de nota
        )

        conn = None
        try:
            # Reutiliza a função de conexão do seu módulo
            conn = db_connector.create_connection(self.db_file) 
            cursor = conn.cursor()
            cursor.execute(sql, new_expense.to_tuple())
            conn.commit()
            return cursor.lastrowid # Retorna o ID da despesa recém-criada
        except sqlite3.Error as e:
            print(f"Erro ao adicionar despesa ao DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: get_expense (Consulta no DB)
    # ----------------------------------------------------
    def get_expense(self, expense_id: int) -> Optional[Dict]:
        """
        Busca uma despesa específica pelo ID.
        """
        sql = "SELECT * FROM expenses WHERE id = ?"
        conn = None
        try:
            conn = db_connector.create_connection(self.db_file)
            cursor = conn.cursor()
            cursor.execute(sql, (expense_id,))
            row = cursor.fetchone()
            
            if row:
                # O row_factory = sqlite3.Row permite aceder por nome
                return dict(row) 
            return None
        except sqlite3.Error as e:
            print(f"Erro ao buscar despesa no DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ----------------------------------------------------
    # TOOL: add_expense_from_document (Orquestração de IA)
    # ----------------------------------------------------
    # A lógica aqui permanece a mesma, pois as chamadas para a IA e a adição final
    # (self.add_expense) já foram tratadas.

    def add_expense_from_document(self, user_id: int, document_text: str) -> Optional[int]:
        """
        Processa texto de um documento/notificação para extrair, classificar e salvar uma despesa.
        """
        # 1. Extração (Chamada à IA)
        extracted_data = self.ai_client.extract_document_data(document_text)
        
        amount = extracted_data.get("amount", 0.0)
        description = extracted_data.get("description", "Descrição não extraída")
        date_str = extracted_data.get("date", datetime.now().strftime('%Y-%m-%d'))

        if amount <= 0:
            return None # Falha na extração de montante

        # 2. Classificação (Chamada à IA)
        category_result = self.ai_client.classify_expense(
            amount=amount,
            description=description,
            categories_list=self.valid_categories
        )
        final_category = category_result.split('\n')[0].strip()
        if final_category not in self.valid_categories:
            final_category = "Outros"   
        # 3. Adição da Despesa (Persistência no DB)
        print(f"Salvando despesa: {description} ({amount}) -> Categoria: {final_category}")
        return self.add_expense(user_id, amount, description, date_str, final_category)