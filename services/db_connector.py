# db_connector.py

import sqlite3 # The actual library for the database

DATABASE_NAME = "unimate.db"

def get_connection():
    """Returns a new connection object to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    # Configure the connection (e.g., set row factory for dictionary-style results)
    return conn

# Or a class for more complex projects (Singleton Pattern is common here)
class DBConnector:
    # ... methods to connect, execute, and close ...
    pass