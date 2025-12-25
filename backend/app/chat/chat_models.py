from database.db_setup import get_db

def create_conversation(user_id, title=None):
    """Create a new conversation for a user."""
    db = get_db()
    cur = db.execute(
        "INSERT INTO conversations (created_by, title) VALUES (?, ?)",
        (user_id, title)
    )
    db.commit()
    return cur.lastrowid

def get_conversation_for_user(conversation_id, user_id):
    """Get a specific conversation if user owns it."""
    db = get_db()
    return db.execute(
        "SELECT * FROM conversations WHERE id = ? AND created_by = ?",
        (conversation_id, user_id)
    ).fetchone()

def get_all_conversations_for_user(user_id):
    """Get all active conversations for a user, sorted by most recent."""
    db = get_db()
    conversations = db.execute('''
        SELECT 
            c.id,
            c.title,
            c.status,
            c.created_at,
            c.updated_at,
            (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
        FROM conversations c
        WHERE c.created_by = ? AND c.status = 'active'
        ORDER BY c.updated_at DESC
    ''', (user_id,)).fetchall()
    return conversations

def get_conversation_messages(conversation_id, user_id):
    """Get all messages for a conversation if user owns it."""
    db = get_db()
    
    # Verify user owns this conversation
    conv = db.execute('''
        SELECT id FROM conversations 
        WHERE id = ? AND created_by = ? AND status = 'active'
    ''', (conversation_id, user_id)).fetchone()
    
    if not conv:
        return None
    
    # Get all messages for this conversation
    messages = db.execute('''
        SELECT 
            id,
            role,
            content,
            tokens,
            created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation_id,)).fetchall()
    
    return messages

def delete_conversation(conversation_id, user_id):
    """Soft delete a conversation (set status to 'deleted')."""
    db = get_db()
    
    # Verify user owns this conversation
    conv = db.execute('''
        SELECT id FROM conversations 
        WHERE id = ? AND created_by = ?
    ''', (conversation_id, user_id)).fetchone()
    
    if not conv:
        return False
    
    # Soft delete
    db.execute('''
        UPDATE conversations 
        SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (conversation_id,))
    db.commit()
    
    return True

def update_conversation_timestamp(conversation_id):
    """Update the updated_at timestamp for a conversation."""
    db = get_db()
    db.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    db.commit()

def insert_message(conversation_id, role, content, sender_user_id=None):
    """Insert a new message into a conversation."""
    db = get_db()
    if sender_user_id is None:
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

def get_default_model_version():
    """Get the default model version ID."""
    db = get_db()
    default_model = db.execute(
        "SELECT id FROM model_versions WHERE is_default = 1 LIMIT 1"
    ).fetchone()
    
    if default_model:
        return default_model["id"]
    
    # Fallback to any available model version
    any_model = db.execute(
        "SELECT id FROM model_versions LIMIT 1"
    ).fetchone()
    
    if any_model:
        return any_model["id"]
    
    return None