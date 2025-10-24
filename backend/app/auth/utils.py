# app/auth/utils.py
import jwt
from datetime import datetime, timedelta
from flask import current_app

def create_access_token(user_id, role, expires_delta=None):
    secret = current_app.config.get("JWT_SECRET", current_app.config.get("SECRET_KEY"))
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),  # ✅ must be string
        "role": role,
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token):
    secret = current_app.config.get("JWT_SECRET", current_app.config.get("SECRET_KEY"))
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except Exception as e:
        return e
