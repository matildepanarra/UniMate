"""
expense_service.py - Manages the registration and query of user expenses using SQLite.
Orchestrates calls to AIService for extraction and categorization.
"""

from typing import Dict, Optional
from datetime import datetime

from langfuse import observe

from services import db_connector
from services.ai_service import AIService

# Tool
from tools.add_expense import add_expense
from tools.get_expense import get_expense
from tools.summarize_expense import summarize_expense


class ExpenseService:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.ai_client = AIService()
        self.valid_categories = ["Grocery", "Transport", "Restaurant", "Leisure", "Home", "Others", "Party", "University","Health"]

    # -------------------------
    # TOOL WRAPPERS
    # -------------------------
    @observe()
    def add_expense(self, user_id: int, amount: float, description: str, date_str: str, category: str) -> Optional[int]:
        if amount <= 0:
            raise ValueError("Amount must be greater than 0.")

        return add_expense(
            db_file=self.db_file,              # ✅ obrigatório
            user_id=user_id,
            amount=amount,
            category=category,
            vendor=description,                # ✅ description -> vendor
            transaction_date=date_str,         # ✅ date_str -> transaction_date
        )

    # CÓDIGO CORRIGIDO/SIMPLIFICADO:
    @observe()
    def get_expense(self, expense_id: int) -> Optional[Dict]:
        # Se a Toolget_expense SEMPRE precisar de db_file, simplesmente passe-o.
        # Isto elimina a inspeção __code__ que causa o erro no mock.
        return get_expense(db_file=self.db_file, expense_id=expense_id)
    
    
    @observe()
    def summarize_expense(self, user_id: int) -> Dict:
        return summarize_expense(db_file=self.db_file, user_id=user_id) \
            if "db_file" in summarize_expense.__code__.co_varnames else summarize_expense(user_id)

    # -------------------------
    # AI ORCHESTRATION
    # -------------------------
    @observe()
    def add_expense_from_document(self, user_id: int, document_text: str) -> Optional[int]:
        extracted = self.ai_client.extract_document_data(document_text)

        amount = float(extracted.get("amount", 0.0) or 0.0)
        description = extracted.get("description", "Description not extracted")
        date_str = extracted.get("date", datetime.now().strftime("%Y-%m-%d"))

        if amount <= 0:
            return None

        category_raw = self.ai_client.classify_expense(
            amount=amount,
            description=description,
            categories_list=self.valid_categories
        )

        final_category = category_raw.split("\n")[0].strip()
        if final_category not in self.valid_categories:
            final_category = "Others"

        return self.add_expense(user_id, amount, description, date_str, final_category)
