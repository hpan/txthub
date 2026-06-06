import os
import psycopg2
import psycopg2.extras

def get_db_url():
    return os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(get_db_url())
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            created_at REAL NOT NULL,
            is_processed BOOLEAN NOT NULL DEFAULT FALSE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS message_tags (
            message_id INTEGER NOT NULL REFERENCES messages(id),
            tag_id INTEGER NOT NULL REFERENCES tags(id),
            PRIMARY KEY (message_id, tag_id)
        )
    ''')
    conn.close()
