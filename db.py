import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "files_db.db")


def get_connection():
    return sqlite3.connect(DB_FILE)     # returns a new sqlite3 connection for each request bcoz sqlite3 connections should be shared across threads. Each thread/request gets its own connection
# Note:- type of error which occurs when we dont do this: 'SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 8382603584 and this is thread id 6109884416'

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        file_type TEXT,
        source_path TEXT,
        destination_path TEXT,
        moved_at TEXT
    )
    """)

    conn.commit()
    conn.close()