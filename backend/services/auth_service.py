"""Business layer: registration and login rules (FR-01, FR-02)."""
import re
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from db import users
from db.connection import connection
from services.errors import ServiceError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8
MAX_PASSWORD = 128
GENERIC_LOGIN_ERROR = "Invalid email or password."   # same for unknown email and wrong password


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def normalize_email(email):
    return _text(email).lower()


def register(name, email, password):
    name = _text(name)
    email = normalize_email(email)
    password = password if isinstance(password, str) else ""

    errors = {}
    if not name:
        errors["displayName"] = "Display name is required."
    if not email:
        errors["email"] = "Email address is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    if not password:
        errors["password"] = "Password is required."
    elif len(password) < MIN_PASSWORD:
        errors["password"] = f"Password must be at least {MIN_PASSWORD} characters."
    elif len(password) > MAX_PASSWORD:
        errors["password"] = f"Password must be at most {MAX_PASSWORD} characters."
    if errors:
        raise ServiceError("Please fix the highlighted fields.", 400, errors)

    with connection() as conn:
        if users.get_by_email(conn, email):
            raise ServiceError("Email address already registered", 409,
                               {"email": "Email address already registered"})
        try:
            user_id = users.create(conn, name, email, generate_password_hash(password))
        except sqlite3.IntegrityError:   # two requests registered the same email at once
            raise ServiceError("Email address already registered", 409,
                               {"email": "Email address already registered"})
    return {"id": user_id, "name": name}


def login(email, password):
    email = normalize_email(email)
    password = password if isinstance(password, str) else ""
    with connection() as conn:
        user = users.get_by_email(conn, email)
    if not user or not check_password_hash(user["password_hash"], password):
        raise ServiceError(GENERIC_LOGIN_ERROR, 401)
    return {"id": user["user_id"], "name": user["name"]}


def get_user(user_id):
    with connection() as conn:
        row = users.get_by_id(conn, user_id)
    return {"id": row["user_id"], "name": row["name"]} if row else None
