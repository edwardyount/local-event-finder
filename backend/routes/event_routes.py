from flask import Blueprint, jsonify, request, session

from services import event_service

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


@events_bp.get("/api/categories")
def list_categories():
    return jsonify(categories=event_service.categories())
