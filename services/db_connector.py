# db_connector.py

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