"""Data layer: the only place that opens the database."""
import os
import sqlite3

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("EVENTS_DB", os.path.join(BACKEND_DIR, "events.db"))
SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")


def get_connection():
    # isolation_level=None -> autocommit; we start transactions ourselves
    # (e.g. "BEGIN IMMEDIATE" for the RSVP capacity check).
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = f.read()
    conn = get_connection()
    try:
        conn.executescript(schema)
    finally:
        conn.close()


from contextlib import contextmanager


@contextmanager
def connection():
    """with connection() as conn: ...  (always closes)"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
