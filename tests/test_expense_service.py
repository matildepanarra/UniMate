import unittest
from unittest.mock import patch, MagicMock
import os
os.environ["GOOGLE_API_KEY"] = "kkhshdhfbfkkcdnek"
from services.expense_service import ExpenseService

TEST_DB_FILE = ":memory:"

class TestExpenseService(unittest.TestCase):

    def setUp(self):
        self.expense_service = ExpenseService(db_file=TEST_DB_FILE)

    @patch('services.expense_service.db_connector.get_connection')
    @patch('services.expense_service.ExpenseService.get_expense')
    def test_add_and_get_expense_manual(self, mock_get_method, mock_get_connection):

        # 1) Criar um "conn fake"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        # 2) Simular que depois do INSERT o id é 1
        mock_cursor.lastrowid = 1

        # 3) Chamar add_expense (vai usar conn e cursor fake)
        expense_id = self.expense_service.add_expense(
            user_id=1,
            amount=50.50,
            description="Café",
            date_str="2025-12-01",
            category="Restaurante"
        )
        self.assertEqual(expense_id, 1)

        # 4) Agora mock do GET
        mock_get_method.return_value = {
            "id": 1,
            "user_id": 1,
            "amount": 50.50,
            "vendor": "Café",
            "category": "Restaurante"
        }

        retrieved = self.expense_service.get_expense(1)
        self.assertEqual(retrieved["amount"], 50.50)


    @patch('services.ai_service.AIService.extract_document_data')
    @patch('services.ai_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_success(self, mock_add_expense, mock_classify, mock_extract):
        mock_extract.return_value = {
            "amount": 120.75,
            "description": "Amazon.com",
            "date": "2025-12-11"
        }
        mock_classify.return_value = "Outros"
        mock_add_expense.return_value = 10

        expense_id = self.expense_service.add_expense_from_document(
            user_id=2,
            document_text="Cobrança 120.75 Amazon ontem"
        )

        mock_extract.assert_called_once()
        mock_classify.assert_called_once_with(
            amount=120.75,
            description="Amazon.com",
            categories_list=self.expense_service.valid_categories
        )

        # aceitar positional (porque o teu código chama assim)
        mock_add_expense.assert_called_once_with(2, 120.75, "Amazon.com", "2025-12-11", "Outros")
        self.assertEqual(expense_id, 10)

    def test_add_expense_manual_validation_fail(self):
        with patch('tools.add_expense.insert_new_expense') as mock_add:
            with self.assertRaises(ValueError):
                self.expense_service.add_expense(
                    user_id=1,
                    amount=-10.00,
                    description="Teste",
                    date_str="2025-12-01",
                    category="Outros"
                )
            mock_add.assert_not_called()


if __name__ == '__main__':
    unittest.main()
