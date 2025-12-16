import sqlite3
import os, hashlib, binascii
from sqlite3 import Error
from typing import Any, Dict, List, Optional, Sequence, Tuple
from datetime import datetime

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
    """Creates the tables (Users, Expenses, Budgets) if they don't exist + runs safe migrations."""
    try:
        cursor = conn.cursor()

        # Tabela 1: USERS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        # MIGRATION SAFE: add password_hash if missing
        cols = cursor.execute("PRAGMA table_info(users);").fetchall()
        col_names = [c["name"] for c in cols]
        if "password_hash" not in col_names:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT;")

        # Tabela 2: EXPENSES
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            vendor TEXT,
            transaction_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)

        # Tabela 3: BUDGETS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount_limit REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, category, start_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)

        conn.commit()
        print("Tables created/migrated successfully.")

    except Error as e:
        print(f"Error creating tables: {e}")
        raise

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



def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return binascii.hexlify(salt).decode() + ":" + binascii.hexlify(dk).decode()

def verify_password(password: str, stored: str) -> bool:
    salt_hex, dk_hex = stored.split(":")
    salt = binascii.unhexlify(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return binascii.hexlify(dk).decode() == dk_hex


def delete_all_budgets_for_user(db_file: str, user_id: int) -> int:
    """
    Elimina todos os registos de orçamento para um user_id específico.
    Devolve o número de linhas eliminadas.
    """
    sql = "DELETE FROM budgets WHERE user_id = ?"
    return execute_modify_query(db_file, sql, (user_id,))


def create_user(conn, name: str, email: str, password: str):
    pw_hash = hash_password(password)
    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, pw_hash, datetime.now().isoformat())
    )
    conn.commit()

def authenticate_user(conn, email: str, password: str):
    row = conn.execute(
        "SELECT id, name, email, password_hash, created_at FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    if not row:
        return None
    if verify_password(password, row["password_hash"]):
        return {"id": row["id"], "name": row["name"], "email": row["email"], "created_at": row["created_at"]}
    return None
