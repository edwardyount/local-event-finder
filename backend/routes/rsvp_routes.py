from flask import Blueprint, jsonify, session

from routes.decorators import login_required
from services import rsvp_service

rsvps_bp = Blueprint("rsvps", __name__, url_prefix="/api/rsvps")


@rsvps_bp.get("")
@login_required
def my_rsvps():
    events = rsvp_service.list_rsvps(session["user_id"])
    return jsonify(events=events, count=len(events))


@rsvps_bp.post("/<int:event_id>")
@login_required
def rsvp(event_id):
    created, event = rsvp_service.rsvp(session["user_id"], event_id)
    return jsonify(created=created, alreadyRSVPed=not created, event=event), (201 if created else 200)
