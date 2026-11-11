"""Application layer: HTTP only. Parse request -> call service -> return JSON."""
from flask import Blueprint, jsonify, request, session

from services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _start_session(user):
    session.clear()                 # avoid session fixation
    session["user_id"] = user["id"]


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    user = auth_service.register(data.get("displayName"), data.get("email"), data.get("password"))
    _start_session(user)
    return jsonify(user=user), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = auth_service.login(data.get("email"), data.get("password"))
    _start_session(user)
    return jsonify(user=user)


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@auth_bp.get("/me")
def me():
    user = auth_service.get_user(session["user_id"]) if "user_id" in session else None
    return jsonify(user=user)       # {"user": null} when signed out
