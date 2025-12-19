import unittest
from unittest.mock import patch, MagicMock
import os

os.environ["GOOGLE_API_KEY"] = "kkhshdhfbfkkcdnek"


from services.expense_service import ExpenseService


TEST_DB_FILE = ":memory:"

class TestExpenseService(unittest.TestCase):
    """
    Testes para a classe ExpenseService, focando-se em mockar as funções
    de ferramenta (Tool) e a lógica de orquestração de IA.
    """

    def setUp(self):
        """Inicializa o serviço antes de cada teste."""
        self.expense_service = ExpenseService(db_file=TEST_DB_FILE)

    @patch('services.expense_service.add_expense') 
    @patch('services.expense_service.get_expense') 
    def test_add_and_get_expense_tool_mock(self, mock_get_expense, mock_add_expense):
        """
        Testa a adição e obtenção de uma despesa, mockando as funções
        de ferramenta de baixo nível (`add_expense` e `get_expense`).
        """
        
        expected_id = 42
        mock_add_expense.return_value = expected_id

        expense_id = self.expense_service.add_expense(
            user_id=1,
            amount=50.50,
            description="Café",
            date_str="2025-12-01",
            category="Restaurant" 
        )
        self.assertEqual(expense_id, expected_id)
        
        mock_add_expense.assert_called_once_with(
            db_file=TEST_DB_FILE,
            user_id=1,
            amount=50.50,
            category="Restaurant",
            vendor="Café",
            transaction_date="2025-12-01",
        )

        mock_expense_data = {
            "id": expected_id,
            "user_id": 1,
            "amount": 50.50,
            "vendor": "Café",
            "category": "Restaurant"
        }
        mock_get_expense.return_value = mock_expense_data


        retrieved = self.expense_service.get_expense(expected_id)
        
        self.assertEqual(retrieved["amount"], 50.50)
        self.assertEqual(retrieved["id"], expected_id)
        
        mock_get_expense.assert_called_once_with(db_file=TEST_DB_FILE, expense_id=expected_id)


    @patch('services.expense_service.AIService.extract_document_data')
    @patch('services.expense_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_success(self, mock_add_expense_method, mock_classify, mock_extract):
        """
        Testa o fluxo de orquestração de IA para adicionar uma despesa a partir de um documento.
        Mocka as chamadas de IA e a chamada interna de `self.add_expense`.
        """
        
        mock_extract.return_value = {
            "amount": 120.75,
            "description": "Amazon.com",
            "date": "2025-12-11"
        }
        
        mock_classify.return_value = "Others\n(Justification)" 
        
        expected_id = 10
        mock_add_expense_method.return_value = expected_id

        document_text = "Cobrança 120.75 Amazon ontem"
        expense_id = self.expense_service.add_expense_from_document(
            user_id=2,
            document_text=document_text
        )


        mock_extract.assert_called_once_with(document_text)
        
        mock_classify.assert_called_once_with(
            amount=120.75,
            description="Amazon.com",
            categories_list=self.expense_service.valid_categories
        )

        mock_add_expense_method.assert_called_once_with(
            2,            
            120.75,       
            "Amazon.com", 
            "2025-12-11",
            "Others"      
        )
        
        self.assertEqual(expense_id, expected_id)

    @patch('services.expense_service.add_expense') 
    def test_add_expense_manual_validation_fail(self, mock_add_expense_tool):
        """
        Testa se a validação (amount <= 0) no `add_expense` do serviço funciona
        corretamente, impedindo a chamada da Tool e levantando um ValueError.
        """
        with self.assertRaises(ValueError) as cm:
            self.expense_service.add_expense(
                user_id=1,
                amount=-10.00, 
                description="Teste",
                date_str="2025-12-01",
                category="Others"
            )
        
        self.assertIn("Amount must be greater than 0.", str(cm.exception))
        

        mock_add_expense_tool.assert_not_called()


    @patch('services.expense_service.AIService.extract_document_data')
    @patch('services.expense_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_invalid_category_fallback(self, mock_add_expense_method, mock_classify, mock_extract):
        """
        Testa se uma categoria inválida retornada pela IA faz o fallback para 'Others'.
        """
 
        mock_extract.return_value = {
            "amount": 10.00,
            "description": "Unknown Vendor",
            "date": "2025-12-01"
        }
        
        mock_classify.return_value = "Random Category" 
        mock_add_expense_method.return_value = 50

        self.expense_service.add_expense_from_document(
            user_id=3,
            document_text="test text"
        )

        mock_add_expense_method.assert_called_once_with(
            3,
            10.00,
            "Unknown Vendor",
            "2025-12-01",
            "Others" 
        )

if __name__ == '__main__':
    unittest.main()