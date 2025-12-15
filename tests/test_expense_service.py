import unittest
from unittest.mock import patch, MagicMock
import os

# Defina a variável de ambiente APENAS se for estritamente necessária
# para a importação de algum módulo (parece ser o caso do 'langfuse' ou 'ai_service'
# que pode depender de uma chave de API para inicialização).
os.environ["GOOGLE_API_KEY"] = "kkhshdhfbfkkcdnek"

# O serviço a ser testado
from services.expense_service import ExpenseService

# O ficheiro de base de dados em memória para testes
TEST_DB_FILE = ":memory:"

class TestExpenseService(unittest.TestCase):
    """
    Testes para a classe ExpenseService, focando-se em mockar as funções
    de ferramenta (Tool) e a lógica de orquestração de IA.
    """

    def setUp(self):
        """Inicializa o serviço antes de cada teste."""
        self.expense_service = ExpenseService(db_file=TEST_DB_FILE)

    @patch('services.expense_service.add_expense') # Mock da função Tool
    @patch('services.expense_service.get_expense') # Mock da função Tool
    def test_add_and_get_expense_tool_mock(self, mock_get_expense, mock_add_expense):
        """
        Testa a adição e obtenção de uma despesa, mockando as funções
        de ferramenta de baixo nível (`add_expense` e `get_expense`).
        """
        
        # 1) Simular o retorno da função add_expense (o ID da nova despesa)
        expected_id = 42
        mock_add_expense.return_value = expected_id

        # 2) Chamar add_expense
        expense_id = self.expense_service.add_expense(
            user_id=1,
            amount=50.50,
            description="Café",
            date_str="2025-12-01",
            category="Restaurant" # Use uma categoria válida
        )
        self.assertEqual(expense_id, expected_id)
        
        # Verificar se a Tool foi chamada com os argumentos CORRETOS
        # Note a adaptação dos nomes dos parâmetros: description -> vendor, date_str -> transaction_date
        mock_add_expense.assert_called_once_with(
            db_file=TEST_DB_FILE,
            user_id=1,
            amount=50.50,
            category="Restaurant",
            vendor="Café",
            transaction_date="2025-12-01",
        )

        # 3) Mockar o retorno da função get_expense
        mock_expense_data = {
            "id": expected_id,
            "user_id": 1,
            "amount": 50.50,
            "vendor": "Café",
            "category": "Restaurant"
        }
        mock_get_expense.return_value = mock_expense_data

        # 4) Chamar get_expense
        retrieved = self.expense_service.get_expense(expected_id)
        
        self.assertEqual(retrieved["amount"], 50.50)
        self.assertEqual(retrieved["id"], expected_id)
        
        # Verificar se a Tool foi chamada. Ajustei a chamada com base
        # na implementação do seu `get_expense` no serviço.
        mock_get_expense.assert_called_once_with(db_file=TEST_DB_FILE, expense_id=expected_id)


    @patch('services.expense_service.AIService.extract_document_data')
    @patch('services.expense_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_success(self, mock_add_expense_method, mock_classify, mock_extract):
        """
        Testa o fluxo de orquestração de IA para adicionar uma despesa a partir de um documento.
        Mocka as chamadas de IA e a chamada interna de `self.add_expense`.
        """
        
        # Simular o output da extração de dados
        mock_extract.return_value = {
            "amount": 120.75,
            "description": "Amazon.com",
            "date": "2025-12-11"
        }
        
        # Simular o output da classificação (deve ser uma das categorias válidas)
        mock_classify.return_value = "Others\n(Justification)" 
        
        # Simular o ID retornado pelo método add_expense do próprio serviço
        expected_id = 10
        mock_add_expense_method.return_value = expected_id

        # Chamar o método em teste
        document_text = "Cobrança 120.75 Amazon ontem"
        expense_id = self.expense_service.add_expense_from_document(
            user_id=2,
            document_text=document_text
        )

        # 1) Verificar as chamadas de IA
        mock_extract.assert_called_once_with(document_text)
        
        mock_classify.assert_called_once_with(
            amount=120.75,
            description="Amazon.com",
            categories_list=self.expense_service.valid_categories
        )

        # 2) Verificar a chamada interna a self.add_expense
        # Nota: Estamos a mockar o método *do serviço*, não a tool.
        # Os argumentos devem ser os que são passados para o método.
        mock_add_expense_method.assert_called_once_with(
            2,            # user_id
            120.75,       # amount
            "Amazon.com", # description
            "2025-12-11", # date_str
            "Others"      # category (limpa e validada)
        )
        
        # 3) Verificar o resultado final
        self.assertEqual(expense_id, expected_id)

    @patch('services.expense_service.add_expense') # Mockar a Tool para garantir que NÃO é chamada
    def test_add_expense_manual_validation_fail(self, mock_add_expense_tool):
        """
        Testa se a validação (amount <= 0) no `add_expense` do serviço funciona
        corretamente, impedindo a chamada da Tool e levantando um ValueError.
        """
        with self.assertRaises(ValueError) as cm:
            self.expense_service.add_expense(
                user_id=1,
                amount=-10.00, # Valor inválido
                description="Teste",
                date_str="2025-12-01",
                category="Others"
            )
        
        self.assertIn("Amount must be greater than 0.", str(cm.exception))
        
        # Verificar que a função Tool NUNCA foi chamada
        mock_add_expense_tool.assert_not_called()

    # Novo teste para a lógica de fallback da classificação
    @patch('services.expense_service.AIService.extract_document_data')
    @patch('services.expense_service.AIService.classify_expense')
    @patch('services.expense_service.ExpenseService.add_expense')
    def test_add_expense_from_document_invalid_category_fallback(self, mock_add_expense_method, mock_classify, mock_extract):
        """
        Testa se uma categoria inválida retornada pela IA faz o fallback para 'Others'.
        """
        
        # Simular extração válida
        mock_extract.return_value = {
            "amount": 10.00,
            "description": "Unknown Vendor",
            "date": "2025-12-01"
        }
        
        # Simular classificação INVÁLIDA
        mock_classify.return_value = "Random Category" 
        mock_add_expense_method.return_value = 50

        # Chamar o método em teste
        self.expense_service.add_expense_from_document(
            user_id=3,
            document_text="test text"
        )
        
        # Verificar se a chamada interna a self.add_expense usou o fallback 'Others'
        mock_add_expense_method.assert_called_once_with(
            3,
            10.00,
            "Unknown Vendor",
            "2025-12-01",
            "Others" # A categoria esperada é 'Others'
        )

if __name__ == '__main__':
    unittest.main()