import unittest
from unittest.mock import patch, MagicMock
from services.expense_service import ExpenseService # Assumimos que o ExpenseService está no services/
from datetime import datetime

# Simulação do caminho para o ficheiro de base de dados para testes
TEST_DB_FILE = ":memory:" # Usamos uma DB SQLite em memória RAM para testes rápidos

class TestExpenseService(unittest.TestCase):

    def setUp(self):
        """Prepara o ambiente antes de cada teste."""
        # Inicializamos o serviço com o DB em memória (o DB real não é usado)
        self.expense_service = ExpenseService(db_file=TEST_DB_FILE)
        
        # O ExpenseService requer que o AIService esteja funcional, 
        # mas vamos mockar (simular) o AIService para não fazermos chamadas reais à API.

    @patch('tools.expense.add_expense.insert_new_expense')
    @patch('tools.expense.get_expense.select_expense_by_id')
    def test_add_and_get_expense_manual(self, mock_get, mock_add):
        """
        Testa a TOOL: add_expense e get_expense.
        Testamos se o serviço chama o tool de DB corretamente.
        """
        # --- Configurar o Mock do ADD ---
        # Simulamos que o tool de DB retorna o ID 1 após a inserção
        mock_add.return_value = 1 
        
        # 1. Chamar o método do Serviço (a lógica de negócio)
        expense_id = self.expense_service.add_expense(
            user_id=1, 
            amount=50.50, 
            description="Café", 
            date_str="2025-12-01", 
            category="Restaurante"
        )
        
        # 2. Assert (Verificação)
        # Verificamos se o serviço chamou o tool de DB exatamente uma vez
        mock_add.assert_called_once()
        # Verificamos se o serviço retornou o ID que o mock simulou
        self.assertEqual(expense_id, 1)

        # --- Configurar o Mock do GET ---
        # Simulamos que o tool de DB retorna uma linha (o dicionário)
        mock_get.return_value = {
            "id": 1, "user_id": 1, "amount": 50.50, "vendor": "Café", "category": "Restaurante"
        }
        
        # 3. Chamar o método do Serviço (get_expense)
        retrieved_expense = self.expense_service.get_expense(1)
        
        # 4. Assert (Verificação)
        mock_get.assert_called_once_with(TEST_DB_FILE, 1) # Verifica se a chamada foi com os args corretos
        self.assertEqual(retrieved_expense['amount'], 50.50)


    @patch('services.ai_service.AIService.extract_document_data')
    @patch('services.ai_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_success(self, mock_add_expense, mock_classify, mock_extract):
        """
        Testa a TOOL: add_expense_from_document. 
        Testamos a ORQUESTRAÇÃO entre o AIService e o ExpenseService.
        """
        # --- Configurar Mocks da IA ---
        mock_extract.return_value = {
            "amount": 120.75, 
            "description": "Amazon.com", 
            "date": "2025-12-11"
        }
        mock_classify.return_value = "Outros"
        
        # --- Configurar Mock do ADD (para finalizar o ciclo) ---
        mock_add_expense.return_value = 10 
        
        # 1. Chamar o Orquestrador
        expense_id = self.expense_service.add_expense_from_document(
            user_id=2, 
            document_text="Cobrança 120.75 Amazon ontem"
        )
        
        # 2. Assert de Orquestração
        # Verificamos se a IA foi chamada para extração
        mock_extract.assert_called_once()
        # Verificamos se a IA foi chamada para categorização com o resultado extraído
        mock_classify.assert_called_once_with(
            amount=120.75, 
            description="Amazon.com", 
            categories_list=self.expense_service.valid_categories
        )
        # Verificamos se o método final de adição foi chamado com os dados limpos
        mock_add_expense.assert_called_once_with(
            user_id=2, 
            amount=120.75, 
            description="Amazon.com", 
            date_str="2025-12-11", 
            category="Outros"
        )
        self.assertEqual(expense_id, 10)

    def test_add_expense_manual_validation_fail(self):
        """
        Testa a lógica de validação: Montante negativo deve falhar.
        """
        # Usamos patch no tool de DB para garantir que ele não é chamado.
        with patch('tools.expense.add_expense.insert_new_expense') as mock_add:
            # Esperamos que o método levante um ValueError
            with self.assertRaises(ValueError):
                self.expense_service.add_expense(
                    user_id=1, 
                    amount=-10.00, # Valor Inválido
                    description="Teste", 
                    date_str="2025-12-01", 
                    category="Outros"
                )
            # Verificamos se o tool de DB NUNCA foi chamado
            mock_add.assert_not_called()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)