import sqlite3
from sqlite3 import Error
import os

DATABASE_FILE = 'unimate_financial_data.db'

def create_connection(db_file=DATABASE_FILE):
    """Cria uma conexão com o banco de dados SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row 
        return conn
    except Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        raise

def create_tables(conn):
    """Cria as tabelas (Users, Expenses, Budgets) se não existirem."""

    # Tabela 1: USERS (Entidade essencial para futuras expansões)
    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL 
    );
    """

    # Tabela 2: EXPENSES (Armazenamento principal de gastos)
    sql_create_expenses_table = """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL, 
        vendor TEXT,
        transaction_date TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """

    # Tabela 3: BUDGETS (Definição de limites de gastos mensais ou por categoria)
    sql_create_budgets_table = """
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL, 
        amount_limit REAL NOT NULL,
        start_date TEXT NOT NULL, -- Início do período (e.g., 'YYYY-MM-01')
        end_date TEXT NOT NULL,   -- Fim do período
        created_at TEXT NOT NULL,
        UNIQUE(user_id, category, start_date),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sql_create_users_table)
        cursor.execute(sql_create_expenses_table)
        cursor.execute(sql_create_budgets_table)
        conn.commit()
        print("Tabelas criadas com sucesso.")
    except Error as e:
        print(f"Erro ao criar tabelas: {e}")
        

def initialize_database():
    """Função principal para inicializar o banco de dados e as tabelas."""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("Não foi possível estabelecer a conexão com o banco de dados.")

if __name__ == '__main__':
    
    initialize_database()


    if os.path.exists(DATABASE_FILE):
        print(f"\nArquivo de banco de dados '{DATABASE_FILE}' criado com sucesso.")