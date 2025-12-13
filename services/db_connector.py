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