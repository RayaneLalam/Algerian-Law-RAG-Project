# app/auth/routes.py
from flask import request, jsonify, current_app, g
from . import bp
from .auth_models import create_user, get_user_by_username, get_user_by_id, verify_password
from .utils import create_access_token, decode_token
from .auth_middleware import jwt_required, admin_required
import json

@bp.route("/register", methods=["POST"])
def register():
    """
    JSON body: {"username": "...", "email": "...", "password": "...", "role": "user" (optional)}
    Role 'admin' is allowed only if:
      - There are no users yet (first sign-up), OR
      - The requester is already an admin (provides admin token).
    Note: username maps to users.display_name in DB for compatibility.
    """
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400

    # If attempting to create admin, check rules:
    if role == "admin":
        from database.db_setup import get_db
        db = get_db()
        row = db.execute("SELECT COUNT(*) as c FROM users").fetchone()
        if row and row["c"] == 0:
            # allow initial admin creation
            pass
        else:
            token = None
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1]
            if not token:
                return jsonify({"error": "Admin creation requires existing admin auth"}), 403
            payload = None
            try:
                payload = decode_token(token)
            except Exception:
                payload = None
            if not payload or payload.get("role") != "admin":
                return jsonify({"error": "Admin creation requires admin privileges"}), 403

    existing = get_user_by_username(username)
    if existing:
        return jsonify({"error": "username already exists"}), 400

    user = create_user(username, email, password, role=role)
    if not user:
        return jsonify({"error": "could not create user (maybe duplicate email)"}), 400

    return jsonify({
        "message": "user created",
        "user_id": user["id"],
        "role": "user"
    }), 201


@bp.route("/login", methods=["POST"])
def login():
    """
    JSON: {"username": "...", "password": "..."}
    Returns: {"access_token": "...", "expires_in": seconds, "role": "...", "user": {...}}
    """
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "invalid credentials"}), 401

    if not verify_password(user, password):
        return jsonify({"error": "invalid credentials"}), 401

    # token expiration: config or default 1 hour
    expires_seconds = int(current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    from datetime import timedelta
    token = create_access_token(user["id"], "user", expires_delta=timedelta(seconds=expires_seconds))

    return jsonify({
        "access_token": token,
        "expires_in": expires_seconds,
        "role": "user",
        "user": {"id": user["id"], "username": user["display_name"], "email": user["email"]}
    }), 200


@bp.route("/me", methods=["GET"])
@jwt_required
def me():
    user = g.current_user
    return jsonify({
        "id": user["id"],
        "username": user["display_name"],
        "email": user["email"],
        "role": "user"
    })


# Example admin-only endpoint
@bp.route("/admin-only", methods=["GET"])
@admin_required
def admin_only():
    return jsonify({"message": "hello admin"}), 200
