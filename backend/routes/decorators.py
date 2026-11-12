from functools import wraps

from flask import jsonify, session


def login_required(view):
    """Server-side check for protected actions (NFR-03). Use under @bp.route."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Login required."), 401
        return view(*args, **kwargs)
    return wrapped
