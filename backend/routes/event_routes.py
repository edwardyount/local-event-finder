from flask import Blueprint, jsonify, request

from services import event_service

events_bp = Blueprint("events", __name__)


@events_bp.get("/api/events")
def browse_events():
    # /api/events?q=park&categories=Education&categories=Food and Drink&startDate=2026-11-14&endDate=2026-11-30
    events = event_service.browse(
        q=request.args.get("q"),
        categories=request.args.getlist("categories"),
        start_date=request.args.get("startDate"),
        end_date=request.args.get("endDate"))
    return jsonify(events=events, count=len(events))


@events_bp.get("/api/categories")
def list_categories():
    return jsonify(categories=event_service.categories())
