# database/db_setup.py
import sqlite3
from flask import g, current_app

def get_db():
    #Get database connection
    if '_database' not in g:
        g._database = sqlite3.connect(current_app.config['DATABASE'])
        g._database.row_factory = sqlite3.Row
        # ensure foreign key constraints are enforced in SQLite
        g._database.execute('PRAGMA foreign_keys = ON;')
    return g._database

def close_connection(exception=None):
    #Close database connection
    db = g.pop('_database', None)
    if db is not None:
        db.close()

def init_db(app):
    #Initialize the database with tables similar to the Supabase schema (SQLite-compatible).
    with app.app_context():
        db = get_db()
        db.executescript('''
            -----------------------------------------------------------------------------
            -- 0) Enums (emulated via CHECK constraints in SQLite)
            -- conversation_status: 'active','archived','deleted'
            -- evaluation_status: 'pending','running','completed','discarded'
            -----------------------------------------------------------------------------

            -----------------------------------------------------------------------------
            -- 1) Auth: roles, users, user_roles
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                display_name TEXT,
                auth_provider_id TEXT,
                profile TEXT DEFAULT '{}' ,          -- JSON stored as TEXT
                is_active INTEGER NOT NULL DEFAULT 1, -- boolean as 0/1
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                granted_by TEXT,
                granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
                FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
            );

            -- seed two roles (user, admin) using INSERT OR IGNORE
            INSERT OR IGNORE INTO roles (id, name, description) VALUES ('role-user', 'user', 'Standard end-user / consumer');
            INSERT OR IGNORE INTO roles (id, name, description) VALUES ('role-admin', 'admin', 'Administrator with elevated privileges');

            -----------------------------------------------------------------------------
            -- 2) Conversations & Messages
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_by TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived','deleted')),
                metadata TEXT DEFAULT '{}' , -- JSON as TEXT
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS conversation_participants (
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                role TEXT,
                PRIMARY KEY (conversation_id, user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender_user_id TEXT,
                model_version_id TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL,
                tokens INTEGER,
                attachments TEXT DEFAULT '[]', -- JSON array as TEXT
                metadata TEXT DEFAULT '{}' ,   -- JSON as TEXT
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_user_id) REFERENCES users(id) ON DELETE SET NULL
                -- model_version_id foreign key created later (model_versions table must exist first)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

            -----------------------------------------------------------------------------
            -- 3) Models: base_models and model_versions
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS base_models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT,
                description TEXT,
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_versions (
                id TEXT PRIMARY KEY,
                base_model_id TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                config TEXT DEFAULT '{}' ,
                artifact_url TEXT,
                trained_at TIMESTAMP,
                created_by TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                performance TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (base_model_id, version),
                FOREIGN KEY (base_model_id) REFERENCES base_models(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_model_versions_base_model ON model_versions(base_model_id);

            -- now that model_versions exists, add foreign key column to messages via a simple pragma-less approach:
            -- Note: SQLite doesn't support ALTER TABLE ... ADD CONSTRAINT. We keep model_version_id as TEXT in messages.
            -- Referential integrity for messages.model_version_id cannot be enforced here without complex migration; it's fine for prototype.

            -----------------------------------------------------------------------------
            -- 4) Datasets & training examples
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                source_type TEXT NOT NULL DEFAULT 'external',
                visibility TEXT NOT NULL DEFAULT 'private',
                metadata TEXT DEFAULT '{}' ,
                created_by TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_training_example (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                gold_label TEXT,
                gold_label_json TEXT,             -- JSON as TEXT
                rlhf_ranked_labels TEXT DEFAULT '[]', -- JSON array as TEXT
                metadata TEXT DEFAULT '{}' ,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_dataset_examples_dataset_id ON dataset_training_example(dataset_id);

            -----------------------------------------------------------------------------
            -- 5) Evaluations & evaluation_candidates
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                evaluator_id TEXT,
                model_version_id TEXT,
                prompt TEXT NOT NULL,
                dataset_example_id TEXT,
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
                id TEXT PRIMARY KEY,
                evaluation_id TEXT NOT NULL,
                model_version_id TEXT,
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

            -----------------------------------------------------------------------------
            -- 6) Metrics Tables
            -----------------------------------------------------------------------------
            CREATE TABLE IF NOT EXISTS metric_types (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_metrics (
                id TEXT PRIMARY KEY,
                model_version_id TEXT NOT NULL,
                dataset_id TEXT,
                metric_type_id TEXT NOT NULL,
                score REAL NOT NULL,
                metadata TEXT DEFAULT '{}' ,
                computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (model_version_id, dataset_id, metric_type_id),
                FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE CASCADE,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL,
                FOREIGN KEY (metric_type_id) REFERENCES metric_types(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_datasets_created_by ON datasets(created_by);

            -----------------------------------------------------------------------------
            -- End of schema
            -----------------------------------------------------------------------------
                         
            -- ---------- Minimal test seed data ----------
            -- Create a test user (evaluator)
            INSERT OR IGNORE INTO users (id, email, display_name, auth_provider_id)
            VALUES ('user-test', 'test@example.com', 'Test User', 'local');

            -- Create a base model and a model version the evaluation can point to
            INSERT OR IGNORE INTO base_models (id, name, provider, description)
            VALUES ('base-model-test', 'mock-base-model', 'local', 'Mock base model for local testing');

            INSERT OR IGNORE INTO model_versions (
                id, base_model_id, version, description, created_by, is_default
            ) VALUES (
                'default-model-v1', 'base-model-test', 'v1', 'Default mock version', 'user-test', 1
            );

            -- Optional: dataset + example if you want to test dataset_example_id paths
            INSERT OR IGNORE INTO datasets (id, title, description, source_type, visibility, created_by)
            VALUES ('dataset-test', 'Mock dataset', 'For local testing', 'external', 'private', 'user-test');

            INSERT OR IGNORE INTO dataset_training_example (id, dataset_id, prompt, gold_label)
            VALUES ('example-test', 'dataset-test', 'Example prompt for testing', 'gold');

        ''')
        db.commit()
