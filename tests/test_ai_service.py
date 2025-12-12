import os
os.environ["GOOGLE_API_KEY"] = "kiubhvuvuvivi"

import unittest
from unittest.mock import patch, MagicMock

from services.ai_service import AIService


class TestAIService(unittest.TestCase):

    @patch("services.ai_service.genai.Client", side_effect=Exception("No API key"))
    def test_init_without_api_key(self, mock_client):
        ai = AIService()
        self.assertIsNone(ai.client)

    def test_extract_document_data_offline(self):
        ai = AIService()
        ai.client = None
        result = ai.extract_document_data("Texto qualquer")
        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["description"], "AI Offline")

    def test_classify_expense_offline(self):
        ai = AIService()
        ai.client = None
        category = ai.classify_expense(20.0, "Uber", ["Transporte", "Restaurante"])
        self.assertEqual(category, "Outros")

    def test_generate_financial_advice_offline(self):
        ai = AIService()
        ai.client = None
        advice = ai.generate_financial_advice({"total": 200})
        self.assertEqual(advice, "Serviço de IA indisponível para aconselhamento.")

    def test_ai_assistant_offline(self):
        ai = AIService()
        ai.client = None
        response = ai.ai_assistant("Quanto gastei este mês?")
        self.assertEqual(response, "Assistente de IA indisponível.")

    def test_predict_future_spending_offline(self):
        ai = AIService()
        ai.client = None
        result = ai.predict_future_spending("{}")
        self.assertEqual(result["predicted_amount"], 0.0)
        self.assertIn("Offline", result["justification"])

    @patch("services.ai_service.genai.Client")
    def test_extract_document_data_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = '{"amount": 45.5, "description": "Amazon", "date": "2025-12-01"}'
        mock_client.models.generate_content.return_value = mock_response

        ai = AIService()
        result = ai.extract_document_data("Amazon 45.50")

        self.assertEqual(result["amount"], 45.5)
        self.assertEqual(result["description"], "Amazon")
        self.assertEqual(result["date"], "2025-12-01")

    @patch("services.ai_service.genai.Client")
    def test_classify_expense_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "Restaurante"
        mock_client.models.generate_content.return_value = mock_response

        ai = AIService()
        category = ai.classify_expense(30, "McDonalds", ["Restaurante", "Outros"])
        self.assertEqual(category, "Restaurante")


if __name__ == "__main__":
    unittest.main(verbosity=2)
