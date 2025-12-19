import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from services.budget_service import BudgetService

TEST_DB_FILE = ":memory:"

class TestBudgetService(unittest.TestCase):
    """
    Testes para a classe BudgetService, focando-se em mockar as funções
    de ferramenta (Tool) e a lógica de orquestração (AI e Business Rules).
    """

    def setUp(self):
        """Inicializa o serviço antes de cada teste."""
        self.service = BudgetService(db_file=TEST_DB_FILE)

        self.patcher_dates = patch(
            "services.budget_service.BudgetService._get_current_month_dates",
            return_value=("2025-12-01", "2026-01-01")
        )
        self.mock_dates = self.patcher_dates.start()
        self.service = BudgetService(db_file=TEST_DB_FILE)
        self.service.ai_client = MagicMock()

    def tearDown(self):
        self.patcher_dates.stop()

    # ----------------------------------------------------
    # set_budget: Testa a delegação correta à Tool
    # ----------------------------------------------------
    @patch("services.budget_service.set_budget_tool.set_budget") 
    def test_set_budget_delegates_to_tool(self, mock_set_budget_tool):
        """
        Testa se set_budget chama a Tool com todos os argumentos corretos,
        incluindo as datas de início e fim calculadas internamente.
        """
        expected_budget_id = 456
        mock_set_budget_tool.return_value = expected_budget_id

        user_id = 1
        category = "Restaurante"
        amount = 200.0

        budget_id = self.service.set_budget(user_id=user_id, category=category, amount_limit=amount)

        self.assertEqual(budget_id, expected_budget_id)
        
        mock_set_budget_tool.assert_called_once_with(
            db_file=TEST_DB_FILE,
            user_id=user_id,
            category=category,
            amount_limit=amount,
            start_date="2025-12-01",
            end_date="2026-01-01",
        )

    # ----------------------------------------------------
    # get_budget_status: Testa a lógica de Business Rules (Status Labels)
    # ----------------------------------------------------
    @patch("services.budget_service.budget_calc_tool.budget_calculator") 
    def test_get_budget_status_status_labels(self, mock_budget_calc_tool):
        """
        Testa as regras de negócio de classificação de status (OK, Atingindo Limite, Excedido, Sem Limite).
        """
        
        mock_budget_calc_tool.return_value = [
            {"category": "OKCat", "amount_limit": 100.0, "spent": 50.0},    
            {"category": "WarnCat", "amount_limit": 100.0, "spent": 85.0},  
            {"category": "OverCat", "amount_limit": 100.0, "spent": 120.0}, 
            {"category": "NoLimit", "amount_limit": 0.0, "spent": 50.0},    
            {"category": "Borderline", "amount_limit": 100.0, "spent": 80.0}, 
        ]

        report = self.service.get_budget_status(user_id=1)

        mock_budget_calc_tool.assert_called_once_with(
            db_file=TEST_DB_FILE,
            user_id=1,
            start_date="2025-12-01",
            end_date="2026-01-01",
        )

        self.assertEqual(len(report), 5)

        by_cat = {r["category"]: r for r in report}
        self.assertEqual(by_cat["OKCat"]["status"], "OK")
        self.assertEqual(by_cat["WarnCat"]["status"], "Atingindo Limite")
        self.assertEqual(by_cat["OverCat"]["status"], "Excedido")
        self.assertEqual(by_cat["NoLimit"]["status"], "Sem limite")
        self.assertEqual(by_cat["Borderline"]["status"], "OK")

    # ----------------------------------------------------
    # analyze_budget: sem histórico -> "Dados insuficientes..."
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.create_connection")
    def test_analyze_budget_insufficient_data(self, mock_create_conn):
        """
        Testa o caso em que não há dados históricos de despesas.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        result = self.service.analyze_budget(user_id=1)

        self.assertIn("Dados insuficientes", result["advice"])
        mock_conn.close.assert_called_once()

        self.service.ai_client.predict_future_spending.assert_not_called()

    # ----------------------------------------------------
    # analyze_budget
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.create_connection")
    def test_analyze_budget_success_flow(self, mock_create_conn):
        """
        Testa a orquestração completa: extração de histórico (SQL), get_budget_status (Tool), AI.
        """

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        historical_rows = [
            ("2025-12-01", 10.0), 
            {"transaction_date": "2025-12-02", "amount": 30.0}, 
        ]
        mock_cursor.fetchall.return_value = historical_rows

        self.service.ai_client = MagicMock()
        prediction_output = {
            "predicted_amount": 100.0,
            "justification": "Mock prediction"
        }
        self.service.ai_client.predict_future_spending.return_value = prediction_output
        self.service.ai_client.generate_financial_advice.return_value = "Mock advice"


        mock_status_report = [{"category": "Restaurante", "limit": 200, "spent": 100, "status": "OK"}]
        with patch.object(self.service, "get_budget_status", return_value=mock_status_report) as mock_status:
            
            result = self.service.analyze_budget(user_id=1)

            self.assertIn("prediction", result)
            self.assertIn("recommendation", result)

            self.assertEqual(result["prediction"]["predicted_amount"], 100.0)
            self.assertEqual(result["recommendation"], "Mock advice")

            mock_status.assert_called_once_with(1)

            expected_historical_data_json_substring = '[{"date": "2025-12-01", "amount": 10.0}, {"date": "2025-12-02", "amount": 30.0}]'
            
            self.service.ai_client.predict_future_spending.assert_called_once()

            call_args = self.service.ai_client.predict_future_spending.call_args[1]
            self.assertIn("historical_data", call_args)
            self.assertIn("prediction_period", call_args)

            expected_context = {
                "prediction": prediction_output,
                "current_budget_status": mock_status_report,
                "recent_spending": [{"date": "2025-12-01", "amount": 10.0}, {"date": "2025-12-02", "amount": 30.0}],
            }
            self.service.ai_client.generate_financial_advice.assert_called_once_with(expected_context)

        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()