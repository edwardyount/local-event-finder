"""Business layer: discovery rules (FR-03, FR-04, FR-05)."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from db import events as events_db
from db.connection import connection
from services.errors import ServiceError

MAX_SEARCH_LENGTH = 200
MAX_CATEGORIES = 20
try:
    EASTERN = ZoneInfo("America/New_York")   # the single event time zone (Q04)
except ZoneInfoNotFoundError:
    # Windows has no system time-zone data; the tzdata package supplies it.
    raise SystemExit("Time zone data missing. Run: pip install -r requirements.txt")


def now_eastern():
    return datetime.now(EASTERN)


def event_status(row, now):
    """cancelled / started / upcoming, judged on the Eastern clock."""
    if row["event_status"] == "cancelled":
        return "cancelled"
    start = f'{row["date"]} {row["start_time"]}'
    return "upcoming" if start > now.strftime("%Y-%m-%d %H:%M") else "started"


def event_to_dict(row, now=None):
    """Shape the frontend already expects (see js/events.js). Never includes the creator's email."""
    now = now or now_eastern()
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
        "status": event_status(row, now),
        "isFavorite": bool(row["is_favorite"]),
        "categoryId": row["category_id"],
        "isOwner": bool(row["is_owner"]),          # is the signed-in user the creator?
        "hasRSVP": bool(row["has_rsvp"]),          # the signed-in user's own RSVP (Q09)
        "seatsLeft": max(row["capacity"] - row["active_rsvp_count"], 0),
    }


def _parse_date(value, field):
    value = (value or "").strip()
    if not value:
        return None                      # blank boundary = unbounded
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ServiceError("Enter a valid date.", 400, {field: "Enter a valid date."})


def browse(q=None, categories=None, start_date=None, end_date=None, user_id=None):
    start = _parse_date(start_date, "startDate")
    end = _parse_date(end_date, "endDate")
    if start and end and end < start:
        raise ServiceError("End date must not be before the start date.", 400,
                           {"endDate": "End date must not be before the start date."})

    q = (q or "").strip().lower()
    if len(q) > MAX_SEARCH_LENGTH:
        raise ServiceError(f"Search text must be {MAX_SEARCH_LENGTH} characters or fewer.", 400,
                           {"q": "Search text is too long."})
    # No duplicates, and never more than a handful (there are only 6 real categories)
    categories = list(dict.fromkeys(c for c in (categories or []) if c.strip()))[:MAX_CATEGORIES]

    now = now_eastern()
    with connection() as conn:
        rows = events_db.search_upcoming(
            conn, now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            q=q, categories=categories, start_date=start, end_date=end, user_id=user_id)
    return [event_to_dict(r, now) for r in rows]


def get_event(event_id, user_id=None):
    with connection() as conn:
        row = events_db.get_by_id(conn, event_id, user_id)
    if not row:
        raise ServiceError("Event not found.", 404)
    return event_to_dict(row)


def categories():
    with connection() as conn:
        return [{"id": r["category_id"], "name": r["category_name"], "image": r["category_image"]}
                for r in events_db.list_categories(conn)]
