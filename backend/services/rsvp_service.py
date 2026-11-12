"""Business layer: RSVP rules (FR-08)."""
from db import events as events_db
from db import rsvps
from db.connection import connection, transaction
from services.errors import ServiceError
from services.event_service import event_status, event_to_dict, now_eastern


def rsvp(user_id, event_id):
    """Returns (created, event). At most one active RSVP per user and event,
    and never more active RSVPs than capacity, even for simultaneous requests."""
    now = now_eastern()
    with transaction() as conn:                       # write lock held until COMMIT
        event = events_db.get_raw(conn, event_id)
        if not event:
            raise ServiceError("Event not found.", 404)

        status = event_status(event, now)
        if status == "cancelled":
            raise ServiceError("This event was cancelled.", 409)
        if status == "started":
            raise ServiceError("This event has already started.", 409)

        if rsvps.get(conn, user_id, event_id):
            created = False                           # repeated request: no duplicate
        else:
            if rsvps.count_active(conn, event_id) >= event["capacity"]:
                raise ServiceError("Event is full.", 409)
            rsvps.insert(conn, user_id, event_id)
            created = True

    with connection() as conn:
        row = events_db.get_by_id(conn, event_id, user_id)
    return created, event_to_dict(row, now)


def list_rsvps(user_id):
    now = now_eastern()
    with connection() as conn:
        rows = rsvps.list_for_user(conn, user_id)
    result = []
    for row in rows:
        item = event_to_dict(row, now)
        item["participation"] = "Confirmed"           # no waitlist or RSVP cancellation in the demo
        result.append(item)
    return result
