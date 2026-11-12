"""Data layer: SQL for the favorites table."""
from db.events import EVENT_SELECT, user_params


def add(conn, user_id, event_id):
    """True if newly saved, False if it was already in this user's favorites."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO favorites (user_id, event_id) VALUES (?, ?)", (user_id, event_id))
    return cur.rowcount == 1


def remove(conn, user_id, event_id):
    """Only ever touches the given user's own row."""
    cur = conn.execute(
        "DELETE FROM favorites WHERE user_id = ? AND event_id = ?", (user_id, event_id))
    return cur.rowcount > 0


def list_for_user(conn, user_id):
    return conn.execute(
        EVENT_SELECT + """
          JOIN favorites fav ON fav.event_id = e.event_id AND fav.user_id = ?
         ORDER BY e.date, e.start_time, e.event_id""",
        user_params(user_id) + [user_id]).fetchall()   # user flags first, then the join
