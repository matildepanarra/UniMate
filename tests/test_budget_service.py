import unittest
from unittest.mock import patch, MagicMock

from services.budget_service import BudgetService


TEST_DB_FILE = ":memory:"


class TestBudgetService(unittest.TestCase):

    def setUp(self):
        # Evita inicializar AI real: vamos substituir ai_client por mock em cada teste quando necessário
        self.service = BudgetService(db_file=TEST_DB_FILE)

    # ----------------------------------------------------
    # set_budget: quando UPDATE não atualiza (rowcount=0) -> faz INSERT
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.get_connection")
    def test_set_budget_inserts_when_no_existing(self, mock_create_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # UPDATE não encontrou linhas
        mock_cursor.rowcount = 0
        # ID retornado após INSERT
        mock_cursor.lastrowid = 123

        budget_id = self.service.set_budget(user_id=1, category="Restaurante", amount_limit=200.0)

        self.assertEqual(budget_id, 123)
        self.assertEqual(mock_cursor.execute.call_count, 2)  # UPDATE + INSERT
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # set_budget: quando UPDATE atualiza (rowcount>0) -> NÃO faz INSERT
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.get_connection")
    def test_set_budget_updates_when_existing(self, mock_create_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # UPDATE afetou 1 linha
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 999  # pode ser qualquer coisa

        budget_id = self.service.set_budget(user_id=1, category="Restaurante", amount_limit=250.0)

        self.assertEqual(budget_id, 999)
        self.assertEqual(mock_cursor.execute.call_count, 1)  # só UPDATE
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # get_budget_status: devolve status OK / Atingindo Limite / Excedido
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.get_connection")
    def test_get_budget_status_status_labels(self, mock_create_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # 3 categorias com cenários diferentes
        # OK: remaining/limit >= 0.2
        # Atingindo Limite: remaining/limit < 0.2 e remaining >= 0
        # Excedido: remaining < 0
        mock_cursor.fetchall.return_value = [
            {"category": "OKCat", "amount_limit": 100.0, "spent": 50.0},    # remaining 50 -> OK
            {"category": "WarnCat", "amount_limit": 100.0, "spent": 85.0},  # remaining 15 -> 0.15 -> Atingindo Limite
            {"category": "OverCat", "amount_limit": 100.0, "spent": 120.0}, # remaining -20 -> Excedido
        ]

        report = self.service.get_budget_status(user_id=1)

        self.assertEqual(len(report), 3)

        by_cat = {r["category"]: r for r in report}
        self.assertEqual(by_cat["OKCat"]["status"], "OK")
        self.assertEqual(by_cat["WarnCat"]["status"], "Atingindo Limite")
        self.assertEqual(by_cat["OverCat"]["status"], "Excedido")

        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # analyze_budget: sem histórico -> "Dados insuficientes..."
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.get_connection")
    def test_analyze_budget_insufficient_data(self, mock_create_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Sem histórico
        mock_cursor.fetchall.return_value = []

        result = self.service.analyze_budget(user_id=1)

        self.assertEqual(result["advice"], "Dados insuficientes para análise de orçamento.")
        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # analyze_budget: com histórico -> chama predict + get_budget_status + generate_financial_advice
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.get_connection")
    def test_analyze_budget_success_flow(self, mock_create_conn):
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Histórico com 2 linhas
        mock_cursor.fetchall.return_value = [
            {"transaction_date": "2025-12-01", "amount": 10.0},
            {"transaction_date": "2025-12-02", "amount": 30.0},
        ]

        # Mock IA
        self.service.ai_client = MagicMock()
        self.service.ai_client.predict_future_spending.return_value = {
            "predicted_amount": 100.0,
            "justification": "Mock prediction"
        }
        self.service.ai_client.generate_financial_advice.return_value = "Mock advice"

        # Mock budget status (não queremos testar SQL aqui)
        with patch.object(self.service, "get_budget_status", return_value=[{"category": "Restaurante", "status": "OK"}]) as mock_status:

            result = self.service.analyze_budget(user_id=1)

            self.assertIn("prediction", result)
            self.assertIn("recommendation", result)

            self.assertEqual(result["prediction"]["predicted_amount"], 100.0)
            self.assertEqual(result["recommendation"], "Mock advice")

            self.service.ai_client.predict_future_spending.assert_called_once()
            self.service.ai_client.generate_financial_advice.assert_called_once()
            mock_status.assert_called_once_with(1)

        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
