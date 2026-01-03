# database/db_setup.py
import sqlite3
from flask import g, current_app

def get_db():
    # Get database connection
    if '_database' not in g:
        g._database = sqlite3.connect(current_app.config['DATABASE'])
        g._database.row_factory = sqlite3.Row
        # ensure foreign key constraints are enforced in SQLite
        g._database.execute('PRAGMA foreign_keys = ON;')
    return g._database

def close_connection(exception=None):
    # Close database connection
    db = g.pop('_database', None)
    if db is not None:
        db.close()

def init_db(app):
    # Initialize the database with tables similar to the Supabase schema (SQLite-compatible).
    with app.app_context():
        db = get_db()
        db.executescript('''
            ---------------------------------------------------------------------
            -- 0) Enums (emulated via CHECK constraints in SQLite)
            ---------------------------------------------------------------------

            ---------------------------------------------------------------------
            -- 1) Auth: roles, users, user_roles
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                auth_provider_id TEXT,
                profile TEXT DEFAULT '{}',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                granted_by INTEGER,
                granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
                FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
            );

            -- seed two roles (user, admin) using INSERT OR IGNORE
            INSERT OR IGNORE INTO roles (id, name, description) VALUES (1, 'user', 'Standard end-user / consumer');
            INSERT OR IGNORE INTO roles (id, name, description) VALUES (2, 'admin', 'Administrator with elevated privileges');

            ---------------------------------------------------------------------
            -- 2) Conversations & Messages
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_by INTEGER,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived','deleted')),
                metadata TEXT DEFAULT '{}' , -- JSON as TEXT
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS conversation_participants (
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                role TEXT,
                PRIMARY KEY (conversation_id, user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_user_id INTEGER,
                model_version_id INTEGER,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL,
                tokens INTEGER,
                attachments TEXT DEFAULT '[]', -- JSON array as TEXT
                metadata TEXT DEFAULT '{}' ,   -- JSON as TEXT
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE SET NULL
                -- model_version_id foreign key depends on model_versions; kept as INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

            ---------------------------------------------------------------------
            -- 3) Models: base_models and model_versions
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS base_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT,
                description TEXT,
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_model_id INTEGER NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                config TEXT DEFAULT '{}' ,
                artifact_url TEXT,
                trained_at TIMESTAMP,
                created_by INTEGER,
                is_default INTEGER NOT NULL DEFAULT 0,
                performance TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (base_model_id, version),
                FOREIGN KEY (base_model_id) REFERENCES base_models(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_model_versions_base_model ON model_versions(base_model_id);

            ---------------------------------------------------------------------
            -- 4) Datasets & training examples
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                source_type TEXT NOT NULL DEFAULT 'external',
                visibility TEXT NOT NULL DEFAULT 'private',
                metadata TEXT DEFAULT '{}' ,
                created_by INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_training_example (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                gold_label TEXT,
                gold_label_json TEXT,             -- JSON as TEXT
                rlhf_ranked_labels TEXT DEFAULT '[]', -- JSON array as TEXT
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_dataset_examples_dataset_id ON dataset_training_example(dataset_id);

            ---------------------------------------------------------------------
            -- 5) Evaluations & evaluation_candidates
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluator_id INTEGER,
                model_version_id INTEGER,
                prompt TEXT NOT NULL,
                dataset_example_id INTEGER,
                num_responses INTEGER NOT NULL DEFAULT 1,
                golden_label TEXT,
                golden_label_json TEXT,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','discarded')),
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (evaluator_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE SET NULL,
                FOREIGN KEY (dataset_example_id) REFERENCES dataset_training_example(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS evaluation_candidate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id INTEGER NOT NULL,
                model_version_id INTEGER,
                response_text TEXT NOT NULL,
                response_json TEXT DEFAULT '{}' , -- JSON as TEXT
                rank_by_evaluator INTEGER CHECK (rank_by_evaluator >= 1),
                evaluator_comment TEXT,
                tokens INTEGER,
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (evaluation_id) REFERENCES evaluations(id) ON DELETE CASCADE,
                FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_evaluation_candidates_eval ON evaluation_candidate(evaluation_id);
            CREATE INDEX IF NOT EXISTS idx_evaluation_candidates_model ON evaluation_candidate(model_version_id);
            CREATE INDEX IF NOT EXISTS idx_evaluations_model_version ON evaluations(model_version_id);

            ---------------------------------------------------------------------
            -- 6) Metrics Tables
            ---------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS metric_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version_id INTEGER NOT NULL,
                dataset_id INTEGER,
                metric_type_id INTEGER NOT NULL,
                score REAL NOT NULL,
                metadata TEXT DEFAULT '{}' ,
                computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (model_version_id, dataset_id, metric_type_id),
                FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE CASCADE,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL,
                FOREIGN KEY (metric_type_id) REFERENCES metric_types(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_datasets_created_by ON datasets(created_by);

            ---------------------------------------------------------------------
            -- End of schema
            ---------------------------------------------------------------------

            -- ---------- Minimal test seed data ----------
            -- Create a test user so that foreign keys for 'created_by' don't fail
            INSERT OR IGNORE INTO users (id, email, password_hash, display_name)
            VALUES (1, 'test@example.com', '123:mock_hash', 'Test User');

            -- Create a base model and a model version the evaluation can point to
            INSERT OR IGNORE INTO base_models (id, name, provider, description)
            VALUES (1, 'mock-base-model', 'local', 'Mock base model for local testing');

            INSERT OR IGNORE INTO model_versions (
                id, base_model_id, version, description, created_by, is_default
            ) VALUES (
                1, 1, 'v1', 'Default mock version', 1, 1
            );

            -- Optional: dataset + example if you want to test dataset_example_id paths
            INSERT OR IGNORE INTO datasets (id, title, description, source_type, visibility, created_by)
            VALUES (1, 'Mock dataset', 'For local testing', 'external', 'private', 1);

            INSERT OR IGNORE INTO dataset_training_example (id, dataset_id, prompt, gold_label)
            VALUES (1, 1, 'Example prompt for testing', 'gold');

        ''')
        db.commit()
