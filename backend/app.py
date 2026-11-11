import os
import secrets

from flask import Flask, jsonify, request, send_from_directory
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf

from db.connection import DB_PATH, init_db
from routes.auth_routes import auth_bp
from routes.event_routes import events_bp
from routes.favorite_routes import favorites_bp
from routes.rsvp_routes import rsvps_bp
from services.errors import ServiceError

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")
SECRET_KEY_FILE = os.environ.get("SECRET_KEY_FILE", os.path.join(BACKEND_DIR, ".secret_key"))

# Only our own scripts and styles may run; images only from our own server.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; img-src 'self' data:; "
    "script-src 'self'; style-src 'self'; form-action 'self'; "
    "base-uri 'self'; frame-ancestors 'none'"
)


def load_secret_key():
    """SECRET_KEY env var, else a random key saved once in backend/.secret_key (never committed).
    A key written in the source code would let anyone forge a login cookie."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    fd = os.open(SECRET_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def create_app():
    # Flask serves the frontend files too, so pages and API share one origin (cookies just work).
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config["SECRET_KEY"] = load_secret_key()
    app.config["SESSION_COOKIE_HTTPONLY"] = True      # page scripts cannot read the session cookie
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"     # not sent on cross-site POSTs
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE") == "1"   # set to 1 behind HTTPS
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024      # no request body over 64 KB
    app.config["WTF_CSRF_TIME_LIMIT"] = None          # token lasts the whole session

    CSRFProtect(app)                                  # NFR-08: all POST/PUT/DELETE need a token

    if not os.path.exists(DB_PATH):
        init_db()

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(rsvps_bp)

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"     # personal data is never cached
        return response

    @app.get("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/api/csrf-token")
    def csrf_token():
        return jsonify(csrfToken=generate_csrf())

    # NFR-07: always JSON errors, never an HTML error page
    @app.errorhandler(ServiceError)
    def service_error(e):
        return jsonify(error=e.message, errors=e.errors), e.status

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return jsonify(error="Invalid or missing CSRF token. Refresh the page and try again."), 400

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found."), 404
        return e                                       # normal 404 for pages

    @app.errorhandler(413)
    def too_large(e):
        return jsonify(error="That request is too large."), 413

    @app.errorhandler(405)
    def method_not_allowed(e):
        if request.path.startswith("/api/"):
            return jsonify(error="Method not allowed."), 405
        return e

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Something went wrong. Please try again."), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Debug mode stays off unless FLASK_DEBUG=1: its error page can run code and
    # replaces our JSON errors. Port 5001, not 5000: macOS AirPlay uses 5000.
    app.run(host="127.0.0.1", port=5001, debug=os.environ.get("FLASK_DEBUG") == "1")
