from flask import Blueprint, jsonify, request, session

from routes.decorators import login_required
from services import event_manage_service, event_service

events_bp = Blueprint("events", __name__)


@events_bp.get("/api/events")
def browse_events():
    # /api/events?q=park&categories=Education&categories=Food and Drink&startDate=2026-11-14&endDate=2026-11-30
    events = event_service.browse(
        q=request.args.get("q"),
        categories=request.args.getlist("categories"),
        start_date=request.args.get("startDate"),
        end_date=request.args.get("endDate"),
        user_id=session.get("user_id"))
    return jsonify(events=events, count=len(events))


@events_bp.get("/api/events/<int:event_id>")
def event_details(event_id):
    return jsonify(event=event_service.get_event(event_id, session.get("user_id")))


@events_bp.post("/api/events")
@login_required
def create_event():
    data = request.get_json(silent=True) or {}
    event = event_manage_service.create_event(session["user_id"], data)
    return jsonify(event=event), 201


@events_bp.put("/api/events/<int:event_id>")
@login_required
def edit_event(event_id):
    data = request.get_json(silent=True) or {}
    event = event_manage_service.update_event(session["user_id"], event_id, data)
    return jsonify(event=event)


@events_bp.get("/api/categories")
def list_categories():
    return jsonify(categories=event_service.categories())
