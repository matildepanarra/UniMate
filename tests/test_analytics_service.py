#import unittest
#from unittest.mock import patch, MagicMock
#
#from services.analytics_service import AnalyticsService
#
#
#class TestAnalyticsService(unittest.TestCase):
#
#    def setUp(self):
#        self.analytics = AnalyticsService(db_file=":memory:")
#
#    # ----------------------------------------------------
#    # TEST: summarize_expense (caso normal)
#    # ----------------------------------------------------
#    @patch("services.analytics_service.db_connector.get_connection")
#    def test_summarize_expense_success(self, mock_get_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#
#        mock_get_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        mock_cursor.fetchall.return_value = [
#            {
#                "total_spent": 200.0,
#                "transaction_count": 4,
#                "avg_transaction_value": 50.0
#            }
#        ]
#
#        result = self.analytics.summarize_expense(user_id=1)
#
#        self.assertEqual(result["total_spent_lifetime"], 200.0)
#        self.assertEqual(result["transaction_count"], 4)
#        self.assertEqual(result["avg_transaction_value"], 50.0)
#
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # TEST: summarize_expense (sem despesas)
#    # ----------------------------------------------------
#    @patch("services.analytics_service.db_connector.get_connection")
#    def test_summarize_expense_empty(self, mock_get_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#
#        mock_get_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        mock_cursor.fetchall.return_value = [
#            {
#                "total_spent": None,
#                "transaction_count": 0,
#                "avg_transaction_value": None
#            }
#        ]
#
#        result = self.analytics.summarize_expense(user_id=1)
#
#        self.assertEqual(result["total_spent_lifetime"], 0.0)
#        self.assertEqual(result["transaction_count"], 0)
#        self.assertEqual(result["avg_transaction_value"], 0.0)
#
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # TEST: get_category_breakdown
#    # ----------------------------------------------------
#    @patch("services.analytics_service.db_connector.get_connection")
#    def test_get_category_breakdown(self, mock_get_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#
#        mock_get_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        mock_cursor.fetchall.return_value = [
#            {"category": "Restaurante", "total_spent": 80.0},
#            {"category": "Outros", "total_spent": 20.0},
#        ]
#
#        result = self.analytics.get_category_breakdown(user_id=1)
#
#        self.assertEqual(result["total_spent_lifetime"], 100.0)
#
#        self.assertEqual(result["Restaurante"]["total"], 80.0)
#        self.assertEqual(result["Restaurante"]["percentage"], 80.0)
#
#        self.assertEqual(result["Outros"]["total"], 20.0)
#        self.assertEqual(result["Outros"]["percentage"], 20.0)
#
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # TEST: get_spending_trends
#    # ----------------------------------------------------
#    @patch("services.analytics_service.db_connector.get_connection")
#    def test_get_spending_trends(self, mock_get_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#
#        mock_get_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        mock_cursor.fetchall.return_value = [
#            {"year_month": "2025-10", "total_spent": 30.0},
#            {"year_month": "2025-11", "total_spent": 70.555},
#        ]
#
#        result = self.analytics.get_spending_trends(user_id=1)
#
#        self.assertEqual(result["period"], "monthly")
#        self.assertEqual(result["data"]["2025-10"], 30.0)
#        self.assertEqual(result["data"]["2025-11"], 70.56)
#
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # TEST: detect_anomalies
#    # ----------------------------------------------------
#    @patch("services.analytics_service.db_connector.get_connection")
#    def test_detect_anomalies(self, mock_get_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#
#        mock_get_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        mock_cursor.fetchall.return_value = [
#            {
#                "id": 10,
#                "amount": 300.0,
#                "vendor": "Apple",
#                "transaction_date": "2025-12-01"
#            },
#            {
#                "id": 11,
#                "amount": 250.0,
#                "vendor": "Amazon",
#                "transaction_date": "2025-12-02"
#            },
#        ]
#
#        result = self.analytics.detect_anomalies(user_id=1)
#
#        self.assertEqual(len(result), 2)
#
#        self.assertEqual(result[0]["expense_id"], 10)
#        self.assertEqual(result[0]["amount"], 300.0)
#        self.assertEqual(result[0]["description"], "Apple")
#        self.assertIn("200%", result[0]["reason"])
#
#        mock_conn.close.assert_called_once()
#
#
#if __name__ == "__main__":
#    unittest.main()
#




import unittest
from unittest.mock import patch, MagicMock

from services.analytics_service import AnalyticsService

# O nome da classe do módulo de serviço
SERVICE_PATH = "services.analytics_service"

class TestAnalyticsService(unittest.TestCase):
    """
    Testes para a classe AnalyticsService, focando-se em:
    1. Mock de DB para métodos internos (summarize, breakdown).
    2. Mock de Tool para métodos delegados (trends, anomalies).
    """

    def setUp(self):
        self.analytics = AnalyticsService(db_file=":memory:")

    # ----------------------------------------------------
    # TEST: summarize_expense (caso normal) - Mock de DB
    # ----------------------------------------------------
    @patch(f"{SERVICE_PATH}._execute_query") # Mock da função interna auxiliar
    def test_summarize_expense_success(self, mock_execute_query):
        """Testa o resumo de despesas com dados válidos."""
        
        # Simular o resultado da query SQL
        mock_execute_query.return_value = [
            {
                "total_spent": 200.0,
                "transaction_count": 4,
                "avg_transaction_value": 50.0
            }
        ]

        result = self.analytics.summarize_expense(user_id=1)

        self.assertEqual(result["total_spent_lifetime"], 200.0)
        self.assertEqual(result["transaction_count"], 4)
        self.assertEqual(result["avg_transaction_value"], 50.0)
        
        # Verificar se a query foi executada
        mock_execute_query.assert_called_once()

    # ----------------------------------------------------
    # TEST: summarize_expense (sem despesas) - Mock de DB
    # ----------------------------------------------------
    @patch(f"{SERVICE_PATH}._execute_query") # Mock da função interna auxiliar
    def test_summarize_expense_empty(self, mock_execute_query):
        """Testa o resumo de despesas quando não há transações."""

        # Simular o resultado da query SQL quando não há dados
        mock_execute_query.return_value = [
            {
                "total_spent": None,
                "transaction_count": 0,
                "avg_transaction_value": None
            }
        ]

        result = self.analytics.summarize_expense(user_id=1)

        self.assertEqual(result["total_spent_lifetime"], 0.0)
        self.assertEqual(result["transaction_count"], 0)
        self.assertEqual(result["avg_transaction_value"], 0.0)
        
        mock_execute_query.assert_called_once()


    # ----------------------------------------------------
    # TEST: get_category_breakdown - Mock de DB + Lógica de Cálculo
    # ----------------------------------------------------
    @patch(f"{SERVICE_PATH}._execute_query") # Mock da função interna auxiliar
    def test_get_category_breakdown(self, mock_execute_query):
        """Testa o cálculo de percentagem e total gasto por categoria."""
        
        # Simular os totais brutos por categoria
        mock_execute_query.return_value = [
            {"category": "Restaurante", "total_spent": 80.0},
            {"category": "Outros", "total_spent": 20.0},
        ]
        
        # Total esperado = 100.0
        result = self.analytics.get_category_breakdown(user_id=1)

        self.assertEqual(result["total_spent_lifetime"], 100.0)

        # Verificação da categoria Restaurante (80/100)
        self.assertEqual(result["Restaurante"]["total"], 80.0)
        self.assertEqual(result["Restaurante"]["percentage"], 80.0)

        # Verificação da categoria Outros (20/100)
        self.assertEqual(result["Outros"]["total"], 20.0)
        self.assertEqual(result["Outros"]["percentage"], 20.0)

        mock_execute_query.assert_called_once()


    # ----------------------------------------------------
    # TEST: get_spending_trends - Mock da Tool
    # ----------------------------------------------------
    @patch("services.analytics_service.get_spending_trend_tool") # Mock da Tool externa
    def test_get_spending_trends_delegation(self, mock_tool):
        """Testa a delegação para a Tool e a transformação do formato de saída."""
        
        # Simular o output RAW da Tool (que é uma Lista de Dicts)
        mock_tool.return_value = [
            {"year_month": "2025-10", "total_spent": 30.0},
            {"year_month": "2025-11", "total_spent": 70.555}, # Testa arredondamento
        ]

        result = self.analytics.get_spending_trends(user_id=1)
        
        # Verifica se a Tool foi chamada corretamente
        mock_tool.assert_called_once_with(self.analytics.db_file, 1)

        # Verifica a transformação de formato (Lista -> Dict com arredondamento)
        self.assertEqual(result["period"], "monthly")
        self.assertDictEqual(result["data"], {
            "2025-10": 30.0,
            "2025-11": 70.56 # Arredondado
        })


    # ----------------------------------------------------
    # TEST: detect_anomalies - Mock da Tool
    # ----------------------------------------------------
    @patch("services.analytics_service.detect_anomalies_tool") # Mock da Tool externa
    def test_detect_anomalies_delegation(self, mock_tool):
        """Testa a delegação para a Tool e a formatação do resultado final."""
        
        # Simular o output RAW da Tool (id, amount, vendor, transaction_date)
        mock_tool.return_value = [
            {
                "id": 10,
                "amount": 300.0,
                "vendor": "Apple",
                "transaction_date": "2025-12-01"
            },
            {
                "id": 11,
                "amount": 250.0,
                "vendor": "Amazon",
                "transaction_date": "2025-12-02"
            },
        ]

        result = self.analytics.detect_anomalies(user_id=1)
        
        # Verifica se a Tool foi chamada corretamente
        mock_tool.assert_called_once_with(self.analytics.db_file, 1)

        # Verifica a formatação do resultado final
        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]["expense_id"], 10)
        self.assertEqual(result[0]["amount"], 300.0)
        self.assertEqual(result[0]["description"], "Apple")
        self.assertEqual(result[0]["reason"], "Value exceeds 200% of the average transaction value.")

        self.assertEqual(result[1]["expense_id"], 11)
        self.assertEqual(result[1]["description"], "Amazon")


if __name__ == "__main__":
    unittest.main()