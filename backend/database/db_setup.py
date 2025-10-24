# database/db_setup.py
import sqlite3
from flask import g, current_app

def get_db():
    """Get database connection"""
    if '_database' not in g:
        g._database = sqlite3.connect(current_app.config['DATABASE'])
        g._database.row_factory = sqlite3.Row
    return g._database

def close_connection(exception=None):
    """Close database connection"""
    db = g.pop('_database', None)
    if db is not None:
        db.close()

def init_db(app):
    """Initialize the database with tables"""
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user',
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
                ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                ON messages(conversation_id);
        ''')
        db.commit()
