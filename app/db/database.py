import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect('data/sql_app.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close() 