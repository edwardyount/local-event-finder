"""Data layer: SQL for events and categories. User input only ever goes in as parameters."""

EVENT_SELECT = """
    SELECT e.event_id, e.title, e.description, e.date, e.start_time, e.end_time,
           e.location, e.capacity, e.event_status,
           c.category_name, c.category_image,
           u.name AS creator_name,
           (SELECT COUNT(*) FROM rsvps r
             WHERE r.event_id = e.event_id AND r.status = 'active') AS active_rsvp_count
      FROM events e
      JOIN categories c ON c.category_id = e.category_id
      JOIN users u      ON u.user_id = e.creator_id
"""


def search_upcoming(conn, now_date, now_time, q=None, categories=None,
                    start_date=None, end_date=None):
    # Upcoming = not cancelled and start is later than "now" (US Eastern).
    sql = EVENT_SELECT + """
     WHERE e.event_status != 'cancelled'
       AND (e.date > ? OR (e.date = ? AND e.start_time > ?))
    """
    params = [now_date, now_date, now_time]

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


def list_categories(conn):
    return conn.execute(
        "SELECT category_id, category_name, category_image FROM categories ORDER BY category_id"
    ).fetchall()
