"""Business layer: creating and editing events (FR-09, FR-10.1)."""
import re
from datetime import datetime

from db import events as events_db
from db import rsvps
from db.connection import connection, transaction
from services.errors import ServiceError
from services.event_service import event_status, event_to_dict, now_eastern

MAX_CAPACITY = 100000
FIX_MESSAGE = "Please fix the highlighted fields."


def _whole_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        return int(value.strip())
    return None


def _parse(value, fmt):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), fmt).strftime(fmt)
    except ValueError:
        return None


def _clean(conn, data, now):
    """Same rules for create and edit. Returns (clean_fields, errors)."""
    data = data if isinstance(data, dict) else {}
    clean, errors = {}, {}

    def text(key, label, limit):
        value = data.get(key)
        value = value.strip() if isinstance(value, str) else ""
        if not value:
            errors[key] = f"{label} is required."
        elif len(value) > limit:
            errors[key] = f"{label} must be at most {limit} characters."
        clean[key] = value

    text("title", "Title", 200)
    text("description", "Description", 5000)
    text("location", "Location", 300)

    category_id = _whole_number(data.get("categoryId"))
    if category_id is None or not events_db.category_exists(conn, category_id):
        errors["categoryId"] = "Choose a category from the list."
    clean["categoryId"] = category_id

    date = _parse(data.get("date"), "%Y-%m-%d")
    start = _parse(data.get("startTime"), "%H:%M")
    end = _parse(data.get("endTime"), "%H:%M")
    if not date:
        errors["date"] = "Enter a valid date."
    if not start:
        errors["startTime"] = "Enter a valid start time."
    if not end:
        errors["endTime"] = "Enter a valid end time."
    clean.update(date=date, startTime=start, endTime=end)

    if start and end and end <= start:
        errors["endTime"] = "End time must be after the start time."
    if date and start and f"{date} {start}" <= now.strftime("%Y-%m-%d %H:%M"):
        errors["startTime"] = "Start must be in the future (US Eastern Time)."

    capacity = _whole_number(data.get("capacity"))
    if capacity is None or capacity < 1 or capacity > MAX_CAPACITY:
        errors["capacity"] = "Capacity must be a whole number greater than 0."
    clean["capacity"] = capacity

    return clean, errors


def create_event(user_id, data):
    now = now_eastern()
    with transaction() as conn:
        clean, errors = _clean(conn, data, now)
        if errors:
            raise ServiceError(FIX_MESSAGE, 400, errors)
        event_id = events_db.insert(conn, user_id, clean)
    with connection() as conn:
        return event_to_dict(events_db.get_by_id(conn, event_id, user_id), now)


def update_event(user_id, event_id, data):
    now = now_eastern()
    with transaction() as conn:
        event = events_db.get_raw(conn, event_id)
        if not event:
            raise ServiceError("Event not found.", 404)
        if event["creator_id"] != user_id:               # ownership is enforced here, on the server
            raise ServiceError("You can only edit your own events.", 403)
        status = event_status(event, now)
        if status != "upcoming":
            raise ServiceError(f"A {status} event can't be edited.", 409)

        clean, errors = _clean(conn, data, now)
        if errors:
            raise ServiceError(FIX_MESSAGE, 400, errors)

        active = rsvps.count_active(conn, event_id)      # counted under the write lock
        if clean["capacity"] < active:
            message = f"Capacity cannot be less than current reservations ({active})."
            raise ServiceError(message, 400, {"capacity": message})

        events_db.update(conn, event_id, clean)
    with connection() as conn:
        return event_to_dict(events_db.get_by_id(conn, event_id, user_id), now)
