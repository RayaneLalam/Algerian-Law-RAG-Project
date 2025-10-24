# app/auth/middleware.py
from functools import wraps
from flask import request, g, jsonify
from .utils import decode_token
from .auth_models import get_user_by_id

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

def admin_required(fn):
    @wraps(fn)
    @jwt_required
    def wrapper(*args, **kwargs):
        role = getattr(g, "current_user_role", None) or g.current_user.get("role")
        if role != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return fn(*args, **kwargs)
    return wrapper
