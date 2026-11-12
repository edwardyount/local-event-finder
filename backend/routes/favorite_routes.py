from flask import Blueprint, jsonify, session

from routes.decorators import login_required
from services import favorite_service

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


@favorites_bp.get("")
@login_required
def list_favorites():
    events = favorite_service.list_favorites(session["user_id"])
    return jsonify(events=events, count=len(events))


@favorites_bp.post("/<int:event_id>")
@login_required
def add_favorite(event_id):
    created = favorite_service.add_favorite(session["user_id"], event_id)
    return jsonify(saved=True, alreadySaved=not created), (201 if created else 200)


@favorites_bp.delete("/<int:event_id>")
@login_required
def remove_favorite(event_id):
    favorite_service.remove_favorite(session["user_id"], event_id)
    return jsonify(removed=True)
