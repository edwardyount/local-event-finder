"""Data layer: SQL for the users table. Parameters only, never string-built SQL."""


def get_by_email(conn, email):
    return conn.execute(
        "SELECT user_id, name, email, password_hash FROM users WHERE email = ?",
        (email,)).fetchone()


def get_by_id(conn, user_id):
    return conn.execute(
        "SELECT user_id, name, email FROM users WHERE user_id = ?",
        (user_id,)).fetchone()


def create(conn, name, email, password_hash):
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash))
    return cur.lastrowid
