#db_connector.py

import sqlite3 # The actual library for the database

DATABASE_NAME = "unimate_financial_data.db"

def get_connection(db_file: str):
    """
    Returns a new connection object to the database.
    """
    conn = sqlite3.connect(db_file)
    return conn

# Or a class for more complex projects (Singleton Pattern is common here)
class DBConnector:
    # ... methods to connect, execute, and close ...
    pass


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

# db_connector.py
#
#import sqlite3
#from sqlite3 import Error
#from typing import Optional, Tuple, List, Dict
#import os
#
## Nome de ficheiro padrão da base de dados (usado se nenhum path for fornecido)
#DEFAULT_DB_FILE = "unimate_financial_data.db" 
#
## --- FUNÇÃO DE CONEXÃO ---
#
#def create_connection(db_file: str = DEFAULT_DB_FILE) -> Optional[sqlite3.Connection]:
#    """
#    Cria e retorna uma conexão com o banco de dados SQLite.
#    
#    Args:
#        db_file: O caminho para o ficheiro DB (usa o padrão se for omitido).
#    
#    Returns:
#        Um objeto Connection configurado para retornar linhas como dicionários (sqlite3.#Row).
#    """
#    conn = None
#    try:
#        conn = sqlite3.connect(db_file) 
#        # ESSENCIAL: Configura a row_factory para que os resultados (cursor.fetchall())
#        # possam ser acedidos como dicionários (row['column_name']).
#        conn.row_factory = sqlite3.Row 
#        return conn
#    except Error as e:
#        # A Langfuse ou outros serviços podem capturar este erro
#        print(f"Erro ao conectar com o banco de dados: {e}") 
#        raise # Re-lançar o erro para que o serviço possa lidar com a falha
#
#
## --- FUNÇÃO DE INICIALIZAÇÃO (NECESSÁRIA PARA TESTES) ---
#
#def initialize_database(db_file: str = DEFAULT_DB_FILE):
#    """
#    Cria as tabelas (users, expenses, budgets) se elas ainda não existirem.
#    """
#    # Definições SQL (Você deve completar com a sua estrutura exata se necessário)
#    sql_create_users_table = """
#    CREATE TABLE IF NOT EXISTS users (
#        id INTEGER PRIMARY KEY,
#        name TEXT NOT NULL,
#        email TEXT UNIQUE NOT NULL,
#        created_at TEXT NOT NULL 
#    );
#    """
#    sql_create_expenses_table = """
#    CREATE TABLE IF NOT EXISTS expenses (
#        id INTEGER PRIMARY KEY,
#        user_id INTEGER NOT NULL,
#        amount REAL NOT NULL,
#        category TEXT NOT NULL, 
#        vendor TEXT,
#        transaction_date TEXT NOT NULL,
#        notes TEXT,
#        created_at TEXT NOT NULL,
#        FOREIGN KEY (user_id) REFERENCES users (id)
#    );
#    """
#    sql_create_budgets_table = """
#    CREATE TABLE IF NOT EXISTS budgets (
#        id INTEGER PRIMARY KEY,
#        user_id INTEGER NOT NULL,
#        category TEXT NOT NULL, 
#        amount_limit REAL NOT NULL,
#        start_date TEXT NOT NULL,
#        end_date TEXT NOT NULL,  
#        created_at TEXT NOT NULL,
#        UNIQUE(user_id, category, start_date),
#        FOREIGN KEY (user_id) REFERENCES users (id)
#    );
#    """
#
#    conn = None
#    try:
#        conn = create_connection(db_file)
#        if conn is not None:
#            cursor = conn.cursor()
#            cursor.execute(sql_create_users_table)
#            cursor.execute(sql_create_expenses_table)
#            cursor.execute(sql_create_budgets_table)
#            conn.commit()
#    except Error as e:
#        print(f"Erro ao criar tabelas: {e}")
#        raise
#    finally:
#        if conn:
#            conn.close()
#
## --- EXPORTAR VARIÁVEL PRINCIPAL ---
## Exportamos o nome do ficheiro principal para ser usado pelo main.py
#DATABASE_FILE = DEFAULT_DB_FILE