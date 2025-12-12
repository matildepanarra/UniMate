import unittest
from unittest.mock import patch, MagicMock

from services.analytics_service import AnalyticsService


class TestAnalyticsService(unittest.TestCase):

    def setUp(self):
        self.analytics = AnalyticsService(db_file=":memory:")

    # ----------------------------------------------------
    # TEST: summarize_expense (caso normal)
    # ----------------------------------------------------
    @patch("services.analytics_service.db_connector.get_connection")
    def test_summarize_expense_success(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
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

        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # TEST: summarize_expense (sem despesas)
    # ----------------------------------------------------
    @patch("services.analytics_service.db_connector.get_connection")
    def test_summarize_expense_empty(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
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

        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # TEST: get_category_breakdown
    # ----------------------------------------------------
    @patch("services.analytics_service.db_connector.get_connection")
    def test_get_category_breakdown(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {"category": "Restaurante", "total_spent": 80.0},
            {"category": "Outros", "total_spent": 20.0},
        ]

        result = self.analytics.get_category_breakdown(user_id=1)

        self.assertEqual(result["total_spent_lifetime"], 100.0)

        self.assertEqual(result["Restaurante"]["total"], 80.0)
        self.assertEqual(result["Restaurante"]["percentage"], 80.0)

        self.assertEqual(result["Outros"]["total"], 20.0)
        self.assertEqual(result["Outros"]["percentage"], 20.0)

        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # TEST: get_spending_trends
    # ----------------------------------------------------
    @patch("services.analytics_service.db_connector.get_connection")
    def test_get_spending_trends(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {"year_month": "2025-10", "total_spent": 30.0},
            {"year_month": "2025-11", "total_spent": 70.555},
        ]

        result = self.analytics.get_spending_trends(user_id=1)

        self.assertEqual(result["period"], "monthly")
        self.assertEqual(result["data"]["2025-10"], 30.0)
        self.assertEqual(result["data"]["2025-11"], 70.56)

        mock_conn.close.assert_called_once()

    # ----------------------------------------------------
    # TEST: detect_anomalies
    # ----------------------------------------------------
    @patch("services.analytics_service.db_connector.get_connection")
    def test_detect_anomalies(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
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

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]["expense_id"], 10)
        self.assertEqual(result[0]["amount"], 300.0)
        self.assertEqual(result[0]["description"], "Apple")
        self.assertIn("200%", result[0]["reason"])

        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
