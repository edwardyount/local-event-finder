import os

from flask import Flask, jsonify, send_from_directory
from flask_wtf.csrf import CSRFError, CSRFProtect, generate_csrf

from db.connection import DB_PATH, init_db
from routes.auth_routes import auth_bp
from services.errors import ServiceError

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def create_app():
    # Flask serves the frontend files too, so pages and API share one origin (cookies just work).
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["WTF_CSRF_TIME_LIMIT"] = None          # token lasts the whole session

    CSRFProtect(app)                                  # NFR-08: all POST/PUT/DELETE need a token

    if not os.path.exists(DB_PATH):
        init_db()

    app.register_blueprint(auth_bp)

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

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Something went wrong. Please try again."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)   # not 5000: macOS AirPlay uses it
