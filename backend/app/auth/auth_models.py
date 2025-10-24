# app/auth/models.py
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_setup import get_db

def ensure_role_column():
    """Add role column if missing (simple safe migration)."""
    db = get_db()
    try:
        # Try a SELECT on role to see if column exists
        db.execute("SELECT role FROM users LIMIT 1")
    except Exception:
        # If it failed, try to add column (SQLite: ALTER TABLE ADD COLUMN)
        try:
            db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            db.commit()
        except Exception:
            # If ALTER fails, ignore (older sqlite or other), but app will still work using default
            pass

def create_user(username, email, password, role="user"):
    db = get_db()
    ensure_role_column()
    pw_hash = generate_password_hash(password)
    try:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, pw_hash, role)
        )
        db.commit()
        return get_user_by_id(cur.lastrowid)
    except Exception as e:
        # Could be UNIQUE constraint violation
        return None

def get_user_by_username(username):
    db = get_db()
    ensure_role_column()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return row

def get_user_by_id(user_id):
    db = get_db()
    ensure_role_column()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row

def verify_password(user_row, password):
    if user_row is None:
        return False
    return check_password_hash(user_row["password_hash"], password)
