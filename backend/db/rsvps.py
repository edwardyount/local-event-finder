"""Data layer: SQL for the rsvps table."""
from db.events import EVENT_SELECT, user_params


def count_active(conn, event_id):
    return conn.execute(
        "SELECT COUNT(*) FROM rsvps WHERE event_id = ? AND status = 'active'",
        (event_id,)).fetchone()[0]


def get(conn, user_id, event_id):
    return conn.execute(
        "SELECT rsvp_id FROM rsvps WHERE user_id = ? AND event_id = ? AND status = 'active'",
        (user_id, event_id)).fetchone()


def insert(conn, user_id, event_id):
    conn.execute("INSERT INTO rsvps (user_id, event_id) VALUES (?, ?)", (user_id, event_id))


def list_for_user(conn, user_id):
    return conn.execute(
        EVENT_SELECT + """
          JOIN rsvps mine ON mine.event_id = e.event_id
                         AND mine.user_id = ? AND mine.status = 'active'
         ORDER BY e.date, e.start_time, e.event_id""",
        user_params(user_id) + [user_id]).fetchall()
