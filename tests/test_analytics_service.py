import unittest
from unittest.mock import patch, MagicMock

from services.analytics_service import AnalyticsService

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
    # TEST: summarize_expense - Mock de DB
    # ----------------------------------------------------
    @patch(f"{SERVICE_PATH}._execute_query") 
    def test_summarize_expense_success(self, mock_execute_query):
        """Testa o resumo de despesas com dados válidos."""
        
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

        mock_execute_query.assert_called_once()

    # ----------------------------------------------------
    # TEST: summarize_expense (sem despesas) - Mock de DB
    # ----------------------------------------------------
    @patch(f"{SERVICE_PATH}._execute_query") # Mock da função interna auxiliar
    def test_summarize_expense_empty(self, mock_execute_query):
        """Testa o resumo de despesas quando não há transações."""

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
    @patch(f"{SERVICE_PATH}._execute_query") 
    def test_get_category_breakdown(self, mock_execute_query):
        """Testa o cálculo de percentagem e total gasto por categoria."""
    
        mock_execute_query.return_value = [
            {"category": "Restaurante", "total_spent": 80.0},
            {"category": "Outros", "total_spent": 20.0},
        ]
        
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
    @patch("services.analytics_service.get_spending_trend_tool") 
    def test_get_spending_trends_delegation(self, mock_tool):
        """Testa a delegação para a Tool e a transformação do formato de saída."""
        
        mock_tool.return_value = [
            {"year_month": "2025-10", "total_spent": 30.0},
            {"year_month": "2025-11", "total_spent": 70.555}, 
        ]

        result = self.analytics.get_spending_trends(user_id=1)
        
        mock_tool.assert_called_once_with(self.analytics.db_file, 1)

        self.assertEqual(result["period"], "monthly")
        self.assertDictEqual(result["data"], {
            "2025-10": 30.0,
            "2025-11": 70.56 
        })

    # ----------------------------------------------------
    # TEST: detect_anomalies - Mock da Tool
    # ----------------------------------------------------
    @patch("services.analytics_service.detect_anomalies_tool") 
    def test_detect_anomalies_delegation(self, mock_tool):
        """Testa a delegação para a Tool e a formatação do resultado final."""
        
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
        
        mock_tool.assert_called_once_with(self.analytics.db_file, 1)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["expense_id"], 10)
        self.assertEqual(result[0]["amount"], 300.0)
        self.assertEqual(result[0]["description"], "Apple")
        self.assertEqual(result[0]["reason"], "Value exceeds 200% of the average transaction value.")

        self.assertEqual(result[1]["expense_id"], 11)
        self.assertEqual(result[1]["description"], "Amazon")


if __name__ == "__main__":
    unittest.main()