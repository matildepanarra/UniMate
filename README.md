# UniMate - AI- powered Financial Assistant for Students 

BRIEF DESCRIPTION OF APPLICATION

## Overview

UniMate is a comprehensive financial management application designed specifically for university students who struggle with managing their personal finances. Many students enter higher education with limited financial literacy and lack access to personalized budgeting tools tailored to their unique circumstances—irregular income from part-time jobs, semester-based expenses, and unpredictable costs.

## Features

- Key feature 1
- Key feature 2
- Key feature 3
- What makes your application unique 

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

##Architecture


UniMate follows a clean architecture pattern with clear separation of concerns across four main layers:
```
unimate/
├── ui/                      # Frontend Layer (Streamlit)
│   ├── pages/              # Application pages
│   │   ├── expense_tracker.py
│   │   ├── budget_manager.py
│   │   ├── analytics.py
│   │   ├── ai_assistant.py
│   │   └── goals.py
│   ├── components/         # Reusable UI components
│   └── app.py             # Main application entry point
│
├── services/               # Business Logic Layer
│   ├── expense_service.py  # Expense CRUD and logic
│   ├── budget_service.py   # Budget management
│   ├── analytics_service.py # Pattern detection and insights
│   └── goal_service.py     # Savings goal tracking
│
├── ai/                     # AI Integration Layer
│   ├── assistant.py        # AI assistant controller
│   ├── prompts.py          # Prompt templates and engineering
│   ├── tools.py            # Function calling tool definitions
│   └── tool_router.py      # Tool routing and execution logic
│
├── models/                 # Data Models
│   ├── expense.py
│   ├── budget.py
│   ├── user.py
│   └── goal.py
│
├── data/                   # Data Access Layer
│   ├── database.py         # Database operations
│   └── storage/            # File storage for receipts
│
├── utils/                  # Utility Functions
│   ├── validators.py       # Data validation
│   ├── formatters.py       # Data formatting
│   └── constants.py        # Application constants
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # Detailed architecture decisions
│   └── diagrams/           # Architecture and data flow diagrams
│
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
└── README.md              # This file

## Installation & Setup

### Prerequisites
- Python 3.x
- API keys for [required services]

### Installation Steps

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [project-name]
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required environment variables:**
```
GOOGLE_API_KEY=AIzaSyDHoic4Vf9hyIOZucYugVAkMZDjYqr7aUk
LANGFUSE_PUBLIC_KEY=pk-lf-2d35a3b0-7ab0-43bd-bb21-4ce72fb52316
LANGFUSE_SECRET_KEY=sk-lf-d28bb517-23f0-464e-b55e-8fa6711d1fbb
LANGFUSE_HOST=https://cloud.langfuse.com

```

4. Run the application:
```bash
uv run streamlit run app.py
```

## Usage

### Tracking Expenses

**Method 1: Manual Entry**
1. Navigate to the "Track Expense" page
2. Fill in: amount, category, date, and description
3. Click "Add Expense"

**Method 2: AI Chat**
Simply tell the assistant in natural language:
- *"I spent €45 at the grocery store today"*
- *"Add €20 for lunch at the cafeteria"*
- *"I bought textbooks for €150"*

**Method 3: Receipt Upload**
1. Go to "Upload Receipt" page
2. Take a photo or upload an image of your receipt
3. Review the automatically extracted information
4. Confirm or edit details as needed

### Managing Budgets

1. Navigate to "Budget Management"
2. Choose a template:
   - **On-Campus Student**: Living in dorms with meal plan
   - **Off-Campus Student**: Independent living expenses
   - **International Student**: Additional costs like travel and insurance
3. Customize category allocations based on your needs
4. Save and monitor progress throughout the month

### Using the AI Assistant

The AI assistant can help with various financial queries:

**Budget Questions:**
- *"How much have I spent on food this month?"*
- *"Am I staying within my entertainment budget?"*
- *"What percentage of my budget have I used?"*

**Financial Advice:**
- *"Give me tips to save more money"*
- *"Should I increase my entertainment budget?"*
- *"How can I reduce my spending on transport?"*

**Goal Planning:**
- *"Help me plan for a €500 emergency fund"*
- *"When can I afford a €1000 laptop?"*
- *"What's the best way to save for spring break?"*

**Analytics & Insights:**
- *"Show me my spending trends"*
- *"What am I spending too much on?"*
- *"How does this month compare to last month?"*

### Viewing Analytics

Navigate to the "Analytics" page to see:
- Spending breakdown by category (pie chart)
- Spending trends over time (line graph)
- Budget vs. actual comparison (bar chart)
- Top spending categories
- Unusual transactions and patterns
- Personalized recommendations

### Setting Savings Goals

1. Go to "Savings Goals" page
2. Click "Create New Goal"
3. Enter: goal name, target amount, and deadline
4. Track progress and receive AI-powered recommendations
5. Adjust your budget based on goal requirements

*Add screenshots or GIFs here to visually demonstrate your application's key features*

## Deployment

**Live Application:** [Your deployed URL]

**Deployment Platform:** [Streamlit Cloud / Render / Vercel / etc.]

### Deploying Your Own Instance

**Streamlit Cloud:**
1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Configure secrets in the Streamlit dashboard:
   - Add all environment variables from `.env`
5. Click "Deploy"

**Other Platforms:**
Ensure your deployment platform supports:
- Python 3.11+
- Environment variable configuration
- File upload capabilities (for receipt processing)



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

**Note:** Component-level READMEs (e.g., `services/README.md`, `tools/README.md`) are recommended if those components need detailed explanation.

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

## License

[Your chosen license - MIT, Apache, etc. - not necessary]

---

## Course Information:

- **Course:** Capstone Project - Bachelor's in Data Science
- **Institution:** NOVA IMS
- **Academic Year:** 2025/2026
- **Professor:** Miguel Cardoso


