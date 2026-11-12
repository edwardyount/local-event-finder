"""Data layer: SQL for events and categories. User input only ever goes in as parameters."""

# Three "?" below belong to the signed-in user (favorite / rsvp / owner flags).
# Anything that uses EVENT_SELECT passes user_params(user_id) first.
EVENT_SELECT = """
    SELECT e.event_id, e.title, e.description, e.date, e.start_time, e.end_time,
           e.location, e.capacity, e.event_status, e.category_id,
           c.category_name, c.category_image,
           u.name AS creator_name,
           (SELECT COUNT(*) FROM rsvps r
             WHERE r.event_id = e.event_id AND r.status = 'active') AS active_rsvp_count,
           EXISTS (SELECT 1 FROM favorites f
                    WHERE f.event_id = e.event_id AND f.user_id = ?) AS is_favorite,
           EXISTS (SELECT 1 FROM rsvps m
                    WHERE m.event_id = e.event_id AND m.user_id = ?
                      AND m.status = 'active') AS has_rsvp,
           (e.creator_id = ?) AS is_owner
      FROM events e
      JOIN categories c ON c.category_id = e.category_id
      JOIN users u      ON u.user_id = e.creator_id
"""


def user_params(user_id):
    return [user_id, user_id, user_id]      # None (signed out) makes all three flags false


def search_upcoming(conn, now_date, now_time, q=None, categories=None,
                    start_date=None, end_date=None, user_id=None):
    # Upcoming = not cancelled and start is later than "now" (US Eastern).
    sql = EVENT_SELECT + """
     WHERE e.event_status != 'cancelled'
       AND (e.date > ? OR (e.date = ? AND e.start_time > ?))
    """
    params = user_params(user_id) + [now_date, now_date, now_time]

    if q:  # literal, case-insensitive substring in title, description or location
        sql += """ AND (instr(lower(e.title), ?) > 0
                     OR instr(lower(e.description), ?) > 0
                     OR instr(lower(e.location), ?) > 0)"""
        params += [q, q, q]
    if categories:  # only "?" placeholders are added to the SQL text, never user text
        sql += " AND c.category_name IN (%s)" % ",".join("?" * len(categories))
        params += categories
    if start_date:
        sql += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND e.date <= ?"
        params.append(end_date)

    sql += " ORDER BY e.date, e.start_time, e.event_id"
    return conn.execute(sql, params).fetchall()


def get_by_id(conn, event_id, user_id=None):
    return conn.execute(EVENT_SELECT + " WHERE e.event_id = ?",
                        user_params(user_id) + [event_id]).fetchone()


def get_raw(conn, event_id):
    """Plain event row, for permission and rule checks."""
    return conn.execute(
        "SELECT event_id, creator_id, date, start_time, capacity, event_status "
        "FROM events WHERE event_id = ?", (event_id,)).fetchone()


def category_exists(conn, category_id):
    return conn.execute("SELECT 1 FROM categories WHERE category_id = ?",
                        (category_id,)).fetchone() is not None


def insert(conn, creator_id, f):
    cur = conn.execute(
        """INSERT INTO events (title, description, date, start_time, end_time,
                               location, capacity, category_id, creator_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (f["title"], f["description"], f["date"], f["startTime"], f["endTime"],
         f["location"], f["capacity"], f["categoryId"], creator_id))
    return cur.lastrowid


def update(conn, event_id, f):
    conn.execute(
        """UPDATE events SET title = ?, description = ?, date = ?, start_time = ?,
                             end_time = ?, location = ?, capacity = ?, category_id = ?
            WHERE event_id = ?""",
        (f["title"], f["description"], f["date"], f["startTime"], f["endTime"],
         f["location"], f["capacity"], f["categoryId"], event_id))


def list_categories(conn):
    return conn.execute(
        "SELECT category_id, category_name, category_image FROM categories ORDER BY category_id"
    ).fetchall()
