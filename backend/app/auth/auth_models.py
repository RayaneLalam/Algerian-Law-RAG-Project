# app/auth/auth_models.py
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_setup import get_db

def ensure_password_column():
    """Add password_hash column if missing (simple safe migration)."""
    db = get_db()
    try:
        db.execute("SELECT password_hash FROM users LIMIT 1")
    except Exception:
        try:
            db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
            db.commit()
        except Exception:
            # If ALTER fails for any reason, ignore — app will behave
            # (password functionality won't work until column exists).
            pass

def create_user(username, email, password=None, role="user", granted_by=None):
    """
    Creates a user (id is INTEGER AUTOINCREMENT). Associates the user with `role`
    via user_roles -> roles. If role doesn't exist it's created.
    Returns the user row (including a 'role' field) or None on failure.
    """
    db = get_db()
    ensure_password_column()
    pw_hash = generate_password_hash(password) if password else None

    try:
        cur = db.execute(
            """
            INSERT INTO users (email, display_name, password_hash, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (email, username, pw_hash)
        )
        user_id = cur.lastrowid

        # find or create role (roles.id is INTEGER)
        role_row = db.execute("SELECT id FROM roles WHERE name = ?", (role,)).fetchone()
        if role_row:
            role_id = role_row["id"]
        else:
            cur_role = db.execute(
                "INSERT INTO roles (name, description, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (role, None)
            )
            role_id = cur_role.lastrowid

        # insert into user_roles (granted_by may be None or integer)
        db.execute(
            "INSERT INTO user_roles (user_id, role_id, granted_by, granted_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, role_id, granted_by)
        )

        db.commit()
        return get_user_by_id(user_id)
    except Exception:
        db.rollback()
        return None

def get_user_by_username(username):
    """
    Look up by display_name (keeps API's 'username' semantics).
    Returns sqlite3.Row with user fields plus 'role' (or None).
    """
    db = get_db()
    ensure_password_column()
    row = db.execute(
        """
        SELECT u.*, r.name AS role
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.display_name = ?
        LIMIT 1
        """,
        (username,)
    ).fetchone()
    return row

def get_user_by_id(user_id):
    db = get_db()
    ensure_password_column()
    row = db.execute(
        """
        SELECT u.*, r.name AS role
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.id = ?
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()
    return row

def verify_password(user_row, password):
    """
    Returns True if password matches. If the user has no password_hash
    (e.g., OAuth user) this returns False.
    """
    if not user_row:
        return False

    # sqlite3.Row supports mapping access, but be defensive
    try:
        pw_hash = user_row["password_hash"]
    except Exception:
        pw_hash = user_row.get("password_hash") if hasattr(user_row, "get") else None

    if not pw_hash:
        return False
    return check_password_hash(pw_hash, password)
