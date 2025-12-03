import json
import os
from ai_services import AIService
from tools.BudgetCalculator import BudgetCalculator
from tools.BussinessHours import BussinessHours
from langfuse import observe

class TicketService:
    """Main Service for processing tickets themselves"""
    
    ROUTINE_RULES = {
        "Authentication": "Auth Team",
        "Billing": "Billing Team",
        "Technical": "Tech Support",
        "Account Management": "Account Team",
        "Sales": "Sales Team",
        "General Support": "Support Team"
    }

    def __init__(self):
        self.ai_service = AIService()
        self.budget_calculator = BudgetCalculator()
        

    @observe()
    def process_ticket(self, ticket_text: str) -> dict:
        """Complete pipeline"""

        classification = self.ai_service.classify_ticket(ticket_text=ticket_text)
        budget_item = self.budget_calculator.calculate_budget(classification["urgency"])

        route_to = self.ROUTINE_RULES.get(
            classification["category"],
            "Support Team"
        )

        in_hours = self.bussiness_hours.is_bussiness_hours()

        final_document = {
            **classification,
            "original_text": ticket_text,
            "budget_item": budget_item,
            "route_to": route_to,
            "in_hours": in_hours
        }

        return final_document
    
if __name__ == "__main__":
    service = TicketService()
    ticket = "I am unable to access my account after the recent update. Please assist."
    result = service.process_ticket(ticket_text=ticket)
    print(json.dumps(result, indent=2))
