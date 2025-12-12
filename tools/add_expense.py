# Lógica Pura: SÓ se preocupa com o BANCO DE DADOS
import sqlite3
import services.db_connector as db_connector
from typing import Optional

def insert_new_expense(db_file: str, user_id: int, amount: float, category: str, vendor: str, transaction_date: str) -> Optional[int]:
    # 1. Montar a QUERY SQL
    sql = "INSERT INTO expenses (user_id, amount, category, vendor, transaction_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))"
    
    # 2. Executar a QUERY no DB
    conn = db_connector.create_connection(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, amount, category, vendor, transaction_date, f"Vendor: {vendor}",))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()