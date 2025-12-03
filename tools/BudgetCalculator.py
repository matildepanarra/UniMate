
from langfuse import observe
import logging

class BudgetCalculator:
    """A simple budget calculator that tracks income and expenses."""

    def __init__(self):
        self.VALUES = {
            "income": 0.0,
            "expenses": 0.0
        }

  #  @observe(as_type="tool")
    def calculate_budget(self):
        """
        Calculate the current budget.

        Args:

        Returns:
            float: The current budget.
        """
        urgency = urgency.lower()

        if urgency not in self.VALUES:
            logging.error(f"Invalid urgency level: {urgency}")
    


    if __name__ == "__main__":
        print("Welcome to the Budget Calculator!")
        calculator = BudgetCalculator()
        print(f"Initial Budget: ${calculator.calculate_budget():.2f}")











from langfuse import observe
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BudgetCalculator:
    """A simple budget calculator that tracks income and expenses with Langfuse observability."""
    
    def __init__(self):
        self.income_items = []
        self.expense_items = []
        logging.info("Budget Calculator initialized")
    
    @observe(as_type="generation")
    def add_income(self, source: str, amount: float):
        """
        Add income to the budget.
        
        Args:
            source (str): The source of income
            amount (float): The amount of income
        
        Returns:
            dict: The added income item
        """
        if amount <= 0:
            logging.error(f"Invalid income amount: {amount}")
            raise ValueError("Income amount must be positive")
        
        income_item = {"source": source, "amount": amount}
        self.income_items.append(income_item)
        logging.info(f"Added income: {source} - ${amount:.2f}")
        return income_item
    
    @observe(as_type="generation")
    def add_expense(self, name: str, amount: float, category: str = "Other"):
        """
        Add an expense to the budget.
        
        Args:
            name (str): The name of the expense
            amount (float): The amount of the expense
            category (str): The category of the expense
        
        Returns:
            dict: The added expense item
        """
        if amount <= 0:
            logging.error(f"Invalid expense amount: {amount}")
            raise ValueError("Expense amount must be positive")
        
        valid_categories = ["Housing", "Food", "Transportation", "Entertainment", 
                          "Utilities", "Healthcare", "Other"]
        
        if category not in valid_categories:
            logging.warning(f"Invalid category '{category}', defaulting to 'Other'")
            category = "Other"
        
        expense_item = {"name": name, "amount": amount, "category": category}
        self.expense_items.append(expense_item)
        logging.info(f"Added expense: {name} - ${amount:.2f} ({category})")
        return expense_item
    
    @observe(as_type="tool")
    def calculate_total_income(self):
        """
        Calculate the total income.
        
        Returns:
            float: The total income
        """
        total = sum(item["amount"] for item in self.income_items)
        logging.info(f"Total income calculated: ${total:.2f}")
        return total
    
    @observe(as_type="tool")
    def calculate_total_expenses(self):
        """
        Calculate the total expenses.
        
        Returns:
            float: The total expenses
        """
        total = sum(item["amount"] for item in self.expense_items)
        logging.info(f"Total expenses calculated: ${total:.2f}")
        return total
    
    @observe(as_type="tool")
    def calculate_budget(self):
        """
        Calculate the current budget (income - expenses).
        
        Returns:
            float: The current budget balance
        """
        income = self.calculate_total_income()
        expenses = self.calculate_total_expenses()
        balance = income - expenses
        logging.info(f"Budget calculated: ${balance:.2f}")
        return balance
    
    @observe(as_type="tool")
    def get_expenses_by_category(self):
        """
        Get expenses grouped by category.
        
        Returns:
            dict: Expenses grouped by category
        """
        categories = {}
        for expense in self.expense_items:
            cat = expense["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(expense)
        
        # Calculate totals for each category
        category_totals = {
            cat: sum(item["amount"] for item in items)
            for cat, items in categories.items()
        }
        
        logging.info(f"Expenses by category: {category_totals}")
        return category_totals
    
    @observe(as_type="generation")
    def get_budget_summary(self):
        """
        Get a complete budget summary.
        
        Returns:
            dict: Complete budget summary
        """
        total_income = self.calculate_total_income()
        total_expenses = self.calculate_total_expenses()
        balance = total_income - total_expenses
        category_breakdown = self.get_expenses_by_category()
        
        summary = {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "status": "surplus" if balance >= 0 else "deficit",
            "category_breakdown": category_breakdown
        }
        
        logging.info("Budget summary generated")
        return summary
    
    def display_summary(self):
        """Display a formatted budget summary."""
        summary = self.get_budget_summary()
        
        print("\n" + "="*50)
        print("BUDGET SUMMARY")
        print("="*50)
        print(f"Total Income:    ${summary['total_income']:>10.2f}")
        print(f"Total Expenses:  ${summary['total_expenses']:>10.2f}")
        print("-"*50)
        print(f"Balance:         ${summary['balance']:>10.2f} ({summary['status'].upper()})")
        print("="*50)
        
        if summary['category_breakdown']:
            print("\nEXPENSES BY CATEGORY:")
            print("-"*50)
            for category, amount in summary['category_breakdown'].items():
                percentage = (amount / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0
                print(f"{category:<20} ${amount:>10.2f} ({percentage:>5.1f}%)")
            print("="*50)


if __name__ == "__main__":
    print("Welcome to the Budget Calculator with Langfuse Observability!")
    print("="*60)
    
    # Create calculator instance
    calculator = BudgetCalculator()
    
    # Add some income
    print("\n📈 Adding Income...")
    calculator.add_income("Salary", 5000.00)
    calculator.add_income("Freelance Work", 1500.00)
    calculator.add_income("Investments", 300.00)
    
    # Add some expenses
    print("\n📉 Adding Expenses...")
    calculator.add_expense("Rent", 1500.00, "Housing")
    calculator.add_expense("Groceries", 400.00, "Food")
    calculator.add_expense("Restaurant", 200.00, "Food")
    calculator.add_expense("Gas", 150.00, "Transportation")
    calculator.add_expense("Netflix", 15.00, "Entertainment")
    calculator.add_expense("Electricity", 100.00, "Utilities")
    calculator.add_expense("Internet", 60.00, "Utilities")
    calculator.add_expense("Doctor Visit", 80.00, "Healthcare")
    
    # Display summary
    calculator.display_summary()
    
    # Calculate final budget
    print(f"\n💰 Final Budget Balance: ${calculator.calculate_budget():.2f}")
    
    print("\n✅ All operations have been tracked with Langfuse!")
    print("Check your Langfuse dashboard to see the observability data.")
