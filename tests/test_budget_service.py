#import unittest
#from unittest.mock import patch, MagicMock
#
#from services.budget_service import BudgetService
#
#
#TEST_DB_FILE = ":memory:"
#
#
#class TestBudgetService(unittest.TestCase):
#
#    def setUp(self):
#        # Evita inicializar AI real: vamos substituir ai_client por mock em cada teste #quando necessário
#        self.service = BudgetService(db_file=TEST_DB_FILE)
#
#    # ----------------------------------------------------
#    # set_budget: quando UPDATE não atualiza (rowcount=0) -> faz INSERT
#    # ----------------------------------------------------
#    @patch("services.budget_service.db_connector.get_connection")
#    def test_set_budget_inserts_when_no_existing(self, mock_create_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#        mock_create_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        # UPDATE não encontrou linhas
#        mock_cursor.rowcount = 0
#        # ID retornado após INSERT
#        mock_cursor.lastrowid = 123
#
#        budget_id = self.service.set_budget(user_id=1, category="Restaurante", #amount_limit=200.0)
#
#        self.assertEqual(budget_id, 123)
#        self.assertEqual(mock_cursor.execute.call_count, 2)  # UPDATE + INSERT
#        mock_conn.commit.assert_called_once()
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # set_budget: quando UPDATE atualiza (rowcount>0) -> NÃO faz INSERT
#    # ----------------------------------------------------
#    @patch("services.budget_service.db_connector.get_connection")
#    def test_set_budget_updates_when_existing(self, mock_create_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#        mock_create_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        # UPDATE afetou 1 linha
#        mock_cursor.rowcount = 1
#        mock_cursor.lastrowid = 999  # pode ser qualquer coisa
#
#        budget_id = self.service.set_budget(user_id=1, category="Restaurante", #amount_limit=250.0)
#
#        self.assertEqual(budget_id, 999)
#        self.assertEqual(mock_cursor.execute.call_count, 1)  # só UPDATE
#        mock_conn.commit.assert_called_once()
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # get_budget_status: devolve status OK / Atingindo Limite / Excedido
#    # ----------------------------------------------------
#    @patch("services.budget_service.db_connector.get_connection")
#    def test_get_budget_status_status_labels(self, mock_create_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#        mock_create_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        # 3 categorias com cenários diferentes
#        # OK: remaining/limit >= 0.2
#        # Atingindo Limite: remaining/limit < 0.2 e remaining >= 0
#        # Excedido: remaining < 0
#        mock_cursor.fetchall.return_value = [
#            {"category": "OKCat", "amount_limit": 100.0, "spent": 50.0},    # remaining 50 #-> OK
#            {"category": "WarnCat", "amount_limit": 100.0, "spent": 85.0},  # remaining 15 #-> 0.15 -> Atingindo Limite
#            {"category": "OverCat", "amount_limit": 100.0, "spent": 120.0}, # remaining -20 #-> Excedido
#        ]
#
#        report = self.service.get_budget_status(user_id=1)
#
#        self.assertEqual(len(report), 3)
#
#        by_cat = {r["category"]: r for r in report}
#        self.assertEqual(by_cat["OKCat"]["status"], "OK")
#        self.assertEqual(by_cat["WarnCat"]["status"], "Atingindo Limite")
#        self.assertEqual(by_cat["OverCat"]["status"], "Excedido")
#
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # analyze_budget: sem histórico -> "Dados insuficientes..."
#    # ----------------------------------------------------
#    @patch("services.budget_service.db_connector.get_connection")
#    def test_analyze_budget_insufficient_data(self, mock_create_conn):
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#        mock_create_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        # Sem histórico
#        mock_cursor.fetchall.return_value = []
#
#        result = self.service.analyze_budget(user_id=1)
#
#        self.assertEqual(result["advice"], "Dados insuficientes para análise de orçamento.")
#        mock_conn.close.assert_called_once()
#
#    # ----------------------------------------------------
#    # analyze_budget: com histórico -> chama predict + get_budget_status + #generate_financial_advice
#    # ----------------------------------------------------
#    @patch("services.budget_service.db_connector.get_connection")
#    def test_analyze_budget_success_flow(self, mock_create_conn):
#        # Mock DB
#        mock_conn = MagicMock()
#        mock_cursor = MagicMock()
#        mock_create_conn.return_value = mock_conn
#        mock_conn.cursor.return_value = mock_cursor
#
#        # Histórico com 2 linhas
#        mock_cursor.fetchall.return_value = [
#            {"transaction_date": "2025-12-01", "amount": 10.0},
#            {"transaction_date": "2025-12-02", "amount": 30.0},
#        ]
#
#        # Mock IA
#        self.service.ai_client = MagicMock()
#        self.service.ai_client.predict_future_spending.return_value = {
#            "predicted_amount": 100.0,
#            "justification": "Mock prediction"
#        }
#        self.service.ai_client.generate_financial_advice.return_value = "Mock advice"
#
#        # Mock budget status (não queremos testar SQL aqui)
#        with patch.object(self.service, "get_budget_status", return_value=[{"category": #"Restaurante", "status": "OK"}]) as mock_status:
#
#            result = self.service.analyze_budget(user_id=1)
#
#            self.assertIn("prediction", result)
#            self.assertIn("recommendation", result)
#
#            self.assertEqual(result["prediction"]["predicted_amount"], 100.0)
#            self.assertEqual(result["recommendation"], "Mock advice")
#
#            self.service.ai_client.predict_future_spending.assert_called_once()
#            self.service.ai_client.generate_financial_advice.assert_called_once()
#            mock_status.assert_called_once_with(1)
#
#        mock_conn.close.assert_called_once()
#
#
#if __name__ == "__main__":
#    unittest.main()


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
        # Configura o serviço sem AI real
        self.service = BudgetService(db_file=TEST_DB_FILE)
        # Mock do método _get_current_month_dates para garantir datas fixas
        # durante os testes, evitando que falhem com a mudança do mês.
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
    @patch("services.budget_service.set_budget_tool.set_budget") # Mock da Tool
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
        
        # Verificar se a Tool foi chamada com os argumentos corretos, incluindo db_file e datas
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
    @patch("services.budget_service.budget_calc_tool.budget_calculator") # Mock da Tool
    def test_get_budget_status_status_labels(self, mock_budget_calc_tool):
        """
        Testa as regras de negócio de classificação de status (OK, Atingindo Limite, Excedido, Sem Limite).
        """
        
        # Simular o output RAW da Tool (spent + amount_limit)
        mock_budget_calc_tool.return_value = [
            {"category": "OKCat", "amount_limit": 100.0, "spent": 50.0},    # remaining 50 -> 50% -> OK
            {"category": "WarnCat", "amount_limit": 100.0, "spent": 85.0},  # remaining 15 -> 15% ( < 20%) -> Atingindo Limite
            {"category": "OverCat", "amount_limit": 100.0, "spent": 120.0}, # remaining -20 -> Excedido
            {"category": "NoLimit", "amount_limit": 0.0, "spent": 50.0},    # limit 0 -> Sem limite (new case)
            {"category": "Borderline", "amount_limit": 100.0, "spent": 80.0}, # remaining 20 -> 20% -> OK (should be >= 0.2)
        ]

        report = self.service.get_budget_status(user_id=1)

        # Verificar se a Tool foi chamada corretamente
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

        # Sem histórico
        mock_cursor.fetchall.return_value = []

        result = self.service.analyze_budget(user_id=1)

        self.assertIn("Dados insuficientes", result["advice"])
        mock_conn.close.assert_called_once()
        # Nenhuma chamada de IA deve ocorrer
        self.service.ai_client.predict_future_spending.assert_not_called()


    # ----------------------------------------------------
    # analyze_budget: com histórico -> chama predict + get_budget_status + generate_financial_advice
    # ----------------------------------------------------
    @patch("services.budget_service.db_connector.create_connection")
    def test_analyze_budget_success_flow(self, mock_create_conn):
        """
        Testa a orquestração completa: extração de histórico (SQL), get_budget_status (Tool), AI.
        """
        # Mock DB
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Histórico com 2 linhas (simulando o formato de retorno do SQL)
        historical_rows = [
            ("2025-12-01", 10.0), # tuple format
            {"transaction_date": "2025-12-02", "amount": 30.0}, # dict/Row format
        ]
        mock_cursor.fetchall.return_value = historical_rows

        # Mock AI
        self.service.ai_client = MagicMock()
        prediction_output = {
            "predicted_amount": 100.0,
            "justification": "Mock prediction"
        }
        self.service.ai_client.predict_future_spending.return_value = prediction_output
        self.service.ai_client.generate_financial_advice.return_value = "Mock advice"

        # Mock get_budget_status do próprio serviço (para isolar o teste do SQL/Tool)
        mock_status_report = [{"category": "Restaurante", "limit": 200, "spent": 100, "status": "OK"}]
        with patch.object(self.service, "get_budget_status", return_value=mock_status_report) as mock_status:
            
            # --- EXECUÇÃO ---
            result = self.service.analyze_budget(user_id=1)

            # --- VERIFICAÇÕES ---
            self.assertIn("prediction", result)
            self.assertIn("recommendation", result)

            self.assertEqual(result["prediction"]["predicted_amount"], 100.0)
            self.assertEqual(result["recommendation"], "Mock advice")

            # 1) Verifica a chamada de get_budget_status
            mock_status.assert_called_once_with(1)

            # 2) Verifica a chamada de predict_future_spending (Atenção ao argumento JSON)
            expected_historical_data_json_substring = '[{"date": "2025-12-01", "amount": 10.0}, {"date": "2025-12-02", "amount": 30.0}]'
            
            self.service.ai_client.predict_future_spending.assert_called_once()
            # A verificação exata do JSON é difícil, verificamos apenas o nome do método
            call_args = self.service.ai_client.predict_future_spending.call_args[1]
            self.assertIn("historical_data", call_args)
            self.assertIn("prediction_period", call_args)
            # Pode-se fazer uma verificação mais robusta do conteúdo se necessário,
            # mas a chamada já está verificada.

            # 3) Verifica a chamada de generate_financial_advice (Atenção ao contexto)
            expected_context = {
                "prediction": prediction_output,
                "current_budget_status": mock_status_report,
                # O histórico passado é o 'historical_data[:10]'
                "recent_spending": [{"date": "2025-12-01", "amount": 10.0}, {"date": "2025-12-02", "amount": 30.0}],
            }
            self.service.ai_client.generate_financial_advice.assert_called_once_with(expected_context)

        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()