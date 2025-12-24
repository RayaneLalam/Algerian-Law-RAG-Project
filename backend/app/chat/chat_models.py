from database.db_setup import get_db

def create_conversation(user_id, title=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO conversations (created_by, title) VALUES (?, ?)",
        (user_id, title)
    )
    db.commit()
    return cur.lastrowid

def get_conversation_for_user(conversation_id, user_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ? AND created_by = ?",
        (conversation_id, user_id)
    ).fetchone()

def update_conversation_timestamp(conversation_id):
    db = get_db()
    db.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    db.commit()

def insert_message(conversation_id, role, content, sender_user_id=None):
    db = get_db()
    if(sender_user_id is None):
        db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
    else:
        db.execute(
            "INSERT INTO messages (conversation_id, role, sender_user_id, content) VALUES (?, ?, ?, ?)",
            (conversation_id, role, sender_user_id, content)
        )
    db.commit()
