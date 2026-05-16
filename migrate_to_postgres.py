import os
import re

APP_PY_PATH = 'app.py'
INIT_DB_PATH = 'init_db.py'
REQ_PATH = 'requirements.txt'

def migrate_app_py():
    with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Replace sqlite3 import with psycopg2
    content = content.replace("import sqlite3", "import psycopg2\nimport psycopg2.extras")
    
    # 2. Update get_db()
    old_get_db = """def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn"""
    
    new_get_db = """class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(db_url)
    return PostgresConnWrapper(conn)"""
    
    content = content.replace(old_get_db, new_get_db)
    
    # 3. Replace sqlite3.IntegrityError
    content = content.replace("sqlite3.IntegrityError", "psycopg2.IntegrityError")
    
    # 4. Replace ? with %s for SQL parameters
    # This is safe because ? is only used for parameters and one comment which doesn't hurt.
    content = content.replace("?", "%s")
    
    with open(APP_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def migrate_init_db():
    with open(INIT_DB_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace sqlite3 with psycopg2
    content = content.replace("import sqlite3", "import psycopg2\nimport psycopg2.extras")
    
    old_conn = """    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        
    conn = sqlite3.connect(DATABASE)"""
    
    new_conn = """    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(db_url)"""
    
    content = content.replace(old_conn, new_conn)
    
    # SQLite AUTOINCREMENT to Postgres SERIAL
    content = content.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    
    # SQLite DATETIME / TIMESTAMP defaults
    # SQLite uses CURRENT_TIMESTAMP, Postgres also supports it.
    # BOOLEAN DEFAULT 0 -> BOOLEAN DEFAULT FALSE
    content = content.replace("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")
    
    with open(INIT_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def migrate_requirements():
    with open(REQ_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'psycopg2-binary' not in content:
        content += "\npsycopg2-binary==2.9.9\n"
    with open(REQ_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    migrate_app_py()
    migrate_init_db()
    migrate_requirements()
    print("Migration of codebase to PostgreSQL completed.")
