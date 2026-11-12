"""Business layer: favorites (FR-07). Every call is scoped to the signed-in user."""
from db import events as events_db
from db import favorites
from db.connection import connection
from services.errors import ServiceError
from services.event_service import event_to_dict, now_eastern


def list_favorites(user_id):
    now = now_eastern()
    with connection() as conn:
        rows = favorites.list_for_user(conn, user_id)
    return [event_to_dict(r, now) for r in rows]


def add_favorite(user_id, event_id):
    """Returns True if newly saved, False if it was already saved (no duplicate, FR-07.2)."""
    with connection() as conn:
        if not events_db.get_by_id(conn, event_id):
            raise ServiceError("Event not found.", 404)
        return favorites.add(conn, user_id, event_id)


def remove_favorite(user_id, event_id):
    with connection() as conn:
        removed = favorites.remove(conn, user_id, event_id)
    if not removed:
        raise ServiceError("That event is not in your favorites.", 404)
