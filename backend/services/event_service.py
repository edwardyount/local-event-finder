"""Business layer: discovery rules (FR-03, FR-04, FR-05)."""
from datetime import datetime
from zoneinfo import ZoneInfo

from db import events as events_db
from db.connection import connection
from services.errors import ServiceError

EASTERN = ZoneInfo("America/New_York")   # the single event time zone (Q04)


def now_eastern():
    return datetime.now(EASTERN)


def event_to_dict(row):
    """Shape the frontend already expects (see js/events.js)."""
    return {
        "id": row["event_id"],
        "title": row["title"],
        "description": row["description"],
        "location": row["location"],
        "category": row["category_name"],
        "categoryImage": row["category_image"],
        "date": row["date"],
        "startTime": row["start_time"],
        "endTime": row["end_time"],
        "creator": row["creator_name"],
        "capacity": row["capacity"],
        "activeRSVPCount": row["active_rsvp_count"],
        "status": row["event_status"],
    }


def _parse_date(value, field):
    value = (value or "").strip()
    if not value:
        return None                      # blank boundary = unbounded
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ServiceError("Enter a valid date.", 400, {field: "Enter a valid date."})


def browse(q=None, categories=None, start_date=None, end_date=None):
    start = _parse_date(start_date, "startDate")
    end = _parse_date(end_date, "endDate")
    if start and end and end < start:
        raise ServiceError("End date must not be before the start date.", 400,
                           {"endDate": "End date must not be before the start date."})

    q = (q or "").strip().lower()
    categories = [c for c in (categories or []) if c.strip()]

    now = now_eastern()
    with connection() as conn:
        rows = events_db.search_upcoming(
            conn, now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            q=q, categories=categories, start_date=start, end_date=end)
    return [event_to_dict(r) for r in rows]


def categories():
    with connection() as conn:
        return [{"id": r["category_id"], "name": r["category_name"], "image": r["category_image"]}
                for r in events_db.list_categories(conn)]
