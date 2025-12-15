"""
#expense_service.py - Manages the registration and query of user expenses using SQLite.
#Orchestrates calls to AIService for extraction and categorization.
#"""
#from typing import List, Dict, Optional
#from datetime import datetime
#import sqlite3
#try:
#    from langfuse import observe  
#except Exception:
#    from utils.observability import observe
#from services import db_connector 
#from services.ai_service import AIService 
#
## 1. MODELS EXPENSE DATA
## Uses a simple dictionary to interact with the DB,
#class Expense:
#    # The class structure reflects the 'expenses' table
#    def __init__(self, user_id: int, amount: float, category: str, vendor: str, 
#                 transaction_date: str, notes: Optional[str] = None, expense_id: Optional[int] = None):
#        self.expense_id = expense_id
#        self.user_id = user_id
#        self.amount = amount
#        self.category = category
#        self.vendor = vendor
#        self.transaction_date = transaction_date 
#        self.notes = notes
#        self.created_at = datetime.now().isoformat()
#
#    @observe()
#    def to_tuple(self):
#        # Used for INSERT into the expenses table
#        return (
#            self.user_id,
#            self.amount,
#            self.category,
#            self.vendor,
#            self.transaction_date,
#            self.notes,
#            self.created_at
#        )
#
## --- 2. EXPENSE SERVICE ---
#class ExpenseService:
#    """
#    Implements a business logic for managing expenses, using SQLite.
#    """
#    def __init__(self, db_file: str):
#        # The connection will be established on each call to be thread-safe (SQLite best practice)
#        self.db_file = db_file 
#        self.ai_client = AIService() 
#        self.valid_categories = ["Grocery", "Transport", "Restaurant", "Leisure", "Home", "Others"]
#
#    # ----------------------------------------------------
#    # TOOL: add_expense (DB persistence)
#    # ----------------------------------------------------
#    @observe()
#    def add_expense(self, user_id: int, amount: float, description: str, date_str: str, category: str) -> Optional[int]:
#        """
#        Inserts a new expense into the 'expenses' table.
#        """
#        sql = """
#        INSERT INTO expenses (user_id, amount, category, vendor, transaction_date, notes, created_at)
#        VALUES (?, ?, ?, ?, ?, ?, ?)
#        """
#        if amount <= 0:
#            raise ValueError("Amount must be greater than 0.")
#        
#        # The 'vendor' field in the DB corresponds to the 'description' in our logic
#        new_expense = Expense(
#            user_id=user_id,
#            amount=amount,
#            category=category,
#            vendor=description,
#            transaction_date=date_str,
#            notes=f"Category classified by AI: {category}" # Example note
#        )
#
#        conn = None
#        try:
#            # Reuses the connection function from your module
#            conn = db_connector.get_connection(self.db_file)
#            cursor = conn.cursor()
#            cursor.execute(sql, new_expense.to_tuple())
#            conn.commit()
#            return cursor.lastrowid 
#        # Returns the ID of the newly created expense
#        except sqlite3.Error as e:
#            print(f"Error adding expense to DB: {e}")
#            return None
#        finally:
#            if conn:
#                conn.close()
#
#    # ----------------------------------------------------
#    # TOOL: get_expense (Consultations on the DB)
#    # ----------------------------------------------------
#    @observe()
#    def get_expense(self, expense_id: int) -> Optional[Dict]:
#        """
#        Search for an expense by ID.
#        """
#        sql = "SELECT * FROM expenses WHERE id = ?"
#        conn = None
#        try:
#            conn = db_connector.create_connection(self.db_file)
#            cursor = conn.cursor()
#            cursor.execute(sql, (expense_id,))
#            row = cursor.fetchone()
#            
#            if row:
#                # The row_factory = sqlite3.Row allows access by name
#                return dict(row) 
#            return None
#        except sqlite3.Error as e:
#            print(f"Error fetching expense from DB: {e}")
#            return None
#        finally:
#            if conn:
#                conn.close()
#
#    # ----------------------------------------------------
#    # TOOL: add_expense_from_document (Orchestration of AI)
#    # ----------------------------------------------------
#    # The logic here remains the same, as the calls to the AI and final addition
#    # (self.add_expense) have already been handled.
#
#    @observe()
#    def add_expense_from_document(self, user_id: int, document_text: str) -> Optional[int]:
#        """
#        Process text from a document/notification to extract, classify and save an expense.
#        """
#        # 1. Extraction (Call to AI)
#        extracted_data = self.ai_client.extract_document_data(document_text)
#        
#        amount = extracted_data.get("amount", 0.0)
#        description = extracted_data.get("description", "Description not extracted")
#        date_str = extracted_data.get("date", datetime.now().strftime('%Y-%m-%d'))
#
#        if amount <= 0:
#            return None # Extraction failed
#
#        # 2. Classification (Call to AI)
#        category_result = self.ai_client.classify_expense(
#            amount=amount,
#            description=description,
#            categories_list=self.valid_categories
#        )
#        final_category = category_result.split('\n')[0].strip()
#        if final_category not in self.valid_categories:
#            final_category = "Others"   
#        # 3. Add Expense (Persistence in DB)
#        print(f"Saving expense: {description} ({amount}) -> Category: {final_category}")
#        return self.add_expense(user_id, amount, description, date_str, final_category)


from typing import Dict, Optional
from datetime import datetime

try:
    from langfuse import observe
except Exception:
    from utils.observability import observe

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
        self.valid_categories = ["Grocery", "Transport", "Restaurant", "Leisure", "Home", "Others"]

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

    @observe()
    def get_expense(self, expense_id: int) -> Optional[Dict]:
        # se a tua tool get_expense também precisar de db_file, diz-me e ajusto
        return get_expense(db_file=self.db_file, expense_id=expense_id) \
            if "db_file" in get_expense.__code__.co_varnames else get_expense(expense_id)

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
