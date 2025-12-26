# app/auth/middleware.py
from functools import wraps
from flask import request, g, jsonify, current_app
from .utils import decode_token
from .auth_models import get_user_by_id
from database.db_setup import get_db
def _get_token_from_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        return None
    parts = auth.split()
    if parts[0].lower() != "bearer" or len(parts) == 1:
        return None
    return parts[1]

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_token_from_header()
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401
        try:
            payload = decode_token(token)
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
        if not payload:
            return jsonify({"error": "Invalid token"}), 401
        user = get_user_by_id(payload.get("sub"))
        if not user:
            return jsonify({"error": "User not found"}), 401
        # Attach user to flask.g
        g.current_user = user
        g.current_user_role = payload.get("role")
        return fn(*args, **kwargs)
    return wrapper

def _user_has_role(user_id: int, role_name: str) -> bool:
    db = get_db()
    cur = db.execute(
        "SELECT 1 FROM roles r "
        "JOIN user_roles ur ON ur.role_id = r.id "
        "WHERE ur.user_id = ? AND r.name = ? LIMIT 1",
        (user_id, role_name)
    )
    return cur.fetchone() is not None

def admin_required(fn):
    @wraps(fn)
    @jwt_required  # keep same style as your original; change to @jwt_required() if you use that form
    def wrapper(*args, **kwargs):
        current_user = getattr(g, "current_user", None)
        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        # robustly get user id whether current_user is a dict or sqlite3.Row
        try:
            user_id = current_user.get("id") if hasattr(current_user, "get") else current_user["id"]
        except Exception:
            return jsonify({"error": "Malformed user object"}), 400

        # shortcut: if middleware earlier set a single role string
        role_hint = getattr(g, "current_user_role", None)
        if role_hint == "admin":
            return fn(*args, **kwargs)

        # if roles were already loaded, use cached set
        cached_roles = getattr(g, "current_user_roles", None)
        if cached_roles:
            if "admin" in cached_roles:
                return fn(*args, **kwargs)
            return jsonify({"error": "Admin privileges required"}), 403

        # otherwise query DB
        try:
            if _user_has_role(user_id, "admin"):
                # cache roles for later use (optional: could load full set)
                g.current_user_roles = {"admin"}
                return fn(*args, **kwargs)
            else:
                return jsonify({"error": "Admin privileges required"}), 403
        except Exception as e:
            current_app.logger.exception("Failed to verify user role")
            return jsonify({"error": "Internal server error"}), 500

    return wrapper
