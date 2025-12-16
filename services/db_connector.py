import sqlite3
import os
from sqlite3 import Error
from typing import Any, Dict, List, Optional, Sequence, Tuple

DATABASE_NAME = "unimate_financial_data.db"
DATABASE_FILE = "unimate_financial_data.db"
def get_connection(db_file: str = DATABASE_FILE):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def create_connection(db_file: str = DATABASE_FILE):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """Criates the tables (Users, Expenses, Budgets) if they don't exist."""

    # Tabela 1: USERS (Entity essential for future expansions)
    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL 
    );
    """

    # Tabela 2: EXPENSES (Storing principal expenses)
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

    # Tabela 3: BUDGETS (Setting monthly or category-based spending limits)
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
        print("Tabels created successfully.")
    except Error as e:
        print(f"Error creating tables: {e}")

def initialize_database():
    """Principal function to initialize the database and tables."""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("It was impossible to establish a connection with the database.")

if __name__ == '__main__':
    
    initialize_database()


    if os.path.exists(DATABASE_FILE):
        print(f"\nNew file '{DATABASE_FILE}' created successfully in the DB.")

def execute_select_query(
    db_file: str,
    sql: str,
    params: Optional[Sequence[Any]] = None
) -> List[Dict]:
    """
    Executa um SELECT e devolve uma lista de dicionários.
    """
    conn = None
    try:
        conn = get_connection(db_file)
        cur = conn.cursor()
        cur.execute(sql, tuple(params or ()))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Error as e:
        print(f"[DB] SELECT error: {e}\nSQL: {sql}\nParams: {params}")
        return []
    finally:
        if conn:
            conn.close()


def execute_modify_query(
    db_file: str,
    sql: str,
    params: Optional[Sequence[Any]] = None
) -> int:
    """
    Executa INSERT/UPDATE/DELETE.
    Devolve lastrowid (INSERT) ou rowcount (UPDATE/DELETE).
    """
    conn = None
    try:
        conn = get_connection(db_file)
        cur = conn.cursor()
        cur.execute(sql, tuple(params or ()))
        conn.commit()

        # Se foi INSERT, lastrowid costuma ser útil
        if sql.strip().upper().startswith("INSERT"):
            return cur.lastrowid

        return cur.rowcount
    except Error as e:
        print(f"[DB] MODIFY error: {e}\nSQL: {sql}\nParams: {params}")
        return -1
    finally:
        if conn:
            conn.close()


# --- Adicionar ao seu db_connector.py ---
def delete_all_budgets_for_user(db_file: str, user_id: int) -> int:
    """
    Elimina todos os registos de orçamento para um user_id específico.
    Devolve o número de linhas eliminadas.
    """
    sql = "DELETE FROM budgets WHERE user_id = ?"
    return execute_modify_query(db_file, sql, (user_id,))