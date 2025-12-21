# UniMate: AI-powered Financial Assistant for Students 

AI-driven assistant that helps students quickly find and apply for financial aid by analyzing their information and documents.


## Overview

UniMate is a comprehensive financial management application designed specifically for university students who struggle with managing their personal finances. Many students enter higher education with limited financial literacy and lack access to personalized budgeting tools tailored to their unique circumstances—irregular income from part-time jobs, semester-based expenses, and unpredictable costs.

## Features

- Expense Tracking
- Budget Management
- Financial Analytics
- AI-Chat Assistant

## Tech Stack

**Backend:**
- Python
- Google Gemini API - LLM for conversational AI and multimodal processing

**Frontend:**
- Streamlit

**AI/ML:**
- Langfuse for observability
- Function calling for AI agent tools
- Multimodal processing for receipt scanning
- Structured output parsing for expense extraction
- Prompt engineering for personalized financial advice 

## Architecture


UniMate follows a clean architecture pattern with clear separation of concerns across four main layers:
```
UNIMATE/
├── ai/                         # Tool callling auxiliar 
│   ├── tools_router.py         # Tool calling logic 
│   └── tools_schema.py         # Tool calling shcema 
│
├── services/                   # Business logic layer
│   ├── ai_service.py           # Gestão da comunicação com LLMs
│   ├── analytics_service.py    # Processamento de insights e padrões
│   ├── budget_service.py       # Regras de gestão de orçamentos
│   ├── db_connector.py         # Ligação central à base de dados
│   └── expense_service.py      # Lógica de gestão de despesas
│
├── tools/                      # Function calling tools
│   ├── add_expense.py          # Registo de novas despesas
│   ├── budget_calculator.py    # Cálculos de limites e poupança
│   ├── detect_anomalies.py     # Identificação de gastos fora do comum
│   ├── get_spending_trend.py   # Análise de tendências temporais
│   └── get expense.py          #
│   └── get_spending_trend
│   └── list_expenses.py
│   └── remove_expense.py
│   └── set_budget.py
│   └── summarize_expense.py
│
├── utils/                      #Utility functions
│   └── tracing.py              #Langfuse configuration
│
|
├── docs/                       # ARCHITECTURE.md
├── tests/                      # Tests 
├── unimate_env/                # Virtual environment 
│
├── app.py                      # Main application entry point (Streamlit UI)
├── unimate_financial_data.db   # Local Database SQLite3
├── pyproject.toml              # Dependencies
└── .env.example                # Environment variable template


## Installation & Setup

### Prerequisites
- Python 3.x
- API keys

### Installation Steps

1. Clone the repository:
```bash
git clone [your-repo-url]
cd UniMate
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your keys
```

**Required environment variables:**
```
GOOGLE_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

```

4. Run the application:
```bash
uv run streamlit run app.py
```

## Usage

### Tracking Expenses

**Method 1: Manual Entry**
1. Navigate to the "Expenses" page
2. Fill in: amount, category, date, and description
3. Click "Add Expense"

**Method 2: AI Chat**
Simply tell the assistant in natural language:
- *"I spent €45 at the grocery store today"*
- *"Add €20 for lunch at the cafeteria"*
- *"I bought textbooks for €150"*

**Method 3: Receipt Upload**
1. Go to "Expenses" page
2. Upload an image of your receipt

### Setting new Budgets

1. Go to "Budget" page
2. Select category and enter value
3. Click "Add new budget"
4. Track progress and receive AI-powered recommendations

### Viewing Analytics

Navigate to the "Analytics" page to see:
- Spending breakdown by category
- Spending trends over time
- Total transactions
- Top spending categories
- Unusual transactions and patterns
- Anomalies detection


### Using the AI Assistant

The AI assistant can help with various financial queries:

**Budget Questions:**
- *"How much have I spent on food this month?"*
- *"Am I staying within my party budget this month?"*

**Financial Advice:**
- *"Give me tips to save more money"*
- *"How can I reduce my spending on transport?"*

**Goal Planning:**
- *"Help me plan for a €500 emergency fund"*
- *"When can I afford a €1000 laptop?"*
- *"What's the best way to save for vacation?"*

**Analytics & Insights:**
- *"Tell me about my spending trends"*
- *"What am I spending too much on?"*


## Deployment

**Live Application:** (https://unimate.streamlit.app)

**Deployment Platform:** Streamlit Cloud

### Deploying Your Own Instance

**Streamlit Cloud:**
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Configure secrets in the Streamlit dashboard:
   - Add all environment variables from `.env`
5. Click "Deploy"


## Project Structure

```
project-root/
├── app.py                 # Main application entry point
├── services/              # Business logic layer
├── tools/                 # Function calling tools
├── utils/                 # Utility functions
├── docs/
│   └── ARCHITECTURE.md    # Architecture decisions and explanations
├── requirements.txt       # Dependencies
├── .env.example          # Environment variable template
└── README.md             # This file
```

## Team

- Matilde Panarra - Full-Stack Development & AI Integration
  - Implemented Gemini API integration, prompt engineering, and function calling tools
  - Developed frontend interface with Streamlit and data visualizations
  - Designed and implemented clean architecture structure


- Constança Sá - Backend Services & Analytics
  - Built service layer and business logic for expenses, budgets, and goals
  - Implemented analytics engine and insights generation
  - Integrated Langfuse observability and monitoring
  - Managed database design and deployment

---

## Course Information:

- **Course:** Capstone Project - Bachelor's in Data Science
- **Institution:** NOVA IMS
- **Academic Year:** 2025/2026
- **Professor:** Miguel Cardoso


