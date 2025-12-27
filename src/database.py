import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import logging
from contextlib import contextmanager

DB_NAME = "financial_memory.db"

@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure they close properly."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Creates the tables if they don't exist."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 1. Transactions Table
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                     id TEXT PRIMARY KEY,
                     date TEXT,
                     description TEXT,
                     amount REAL,
                     category TEXT,
                     account TEXT
                     )''')
        
        # 2. Balance History
        c.execute('''CREATE TABLE IF NOT EXISTS balance_history (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     date TEXT,
                     account TEXT,
                     balance REAL
                     )''')
        conn.commit()

def clear_db():
    """Wipes the database for a fresh reload."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM transactions")
            c.execute("DELETE FROM balance_history")
            conn.commit()
        logging.info("🧹 Database wiped for fresh reload.")
    except Exception as e:
        logging.warning(f"DB Reset failed: {e}")

def save_transaction(date, desc, amount, category, account):
    """
    Saves a transaction. Returns True if new, False if duplicate.
    Uses MD5 hashing of the content to create a unique ID.
    """
    # Normalize data for hash consistency
    unique_str = f"{date}{desc.strip().lower()}{amount}{account}"
    tx_id = hashlib.md5(unique_str.encode()).hexdigest()
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
                      (tx_id, date, desc, amount, category, account))
            conn.commit()
            return True 
    except sqlite3.IntegrityError:
        return False # Duplicate detected

def save_balance_snapshot(account, balance):
    """
    Saves a balance checkpoint. 
    Logic: Only save one snapshot per account per day to keep the graph clean.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    with get_db_connection() as conn:
        c = conn.cursor()
        # Check if we already have a snapshot for today
        c.execute("SELECT id FROM balance_history WHERE date=? AND account=?", (today, account))
        if not c.fetchone():
            c.execute("INSERT INTO balance_history (date, account, balance) VALUES (?, ?, ?)",
                      (today, account, balance))
            conn.commit()

def get_net_worth_history():
    """Fetches historical balance data for plotting."""
    with get_db_connection() as conn:
        return pd.read_sql("SELECT date, account, balance FROM balance_history ORDER BY date ASC", conn)

def get_all_transactions():
    """Returns all historical transactions for context."""
    with get_db_connection() as conn:
        return pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", conn)