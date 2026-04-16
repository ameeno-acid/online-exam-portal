import sqlite3

DATABASE = 'database.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys=off;')

    # 1. Update users table with new role constraint and status column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            session_token TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Copy existing data, defaulting status to 'approved' for old users
    cursor.execute('''
        INSERT INTO users_new (id, name, email, password_hash, role, session_token, status, created_at)
        SELECT id, name, email, password_hash, role, session_token, 'approved', created_at FROM users
    ''')
    cursor.execute('DROP TABLE users')
    cursor.execute('ALTER TABLE users_new RENAME TO users')
    
    # 2. Add cheated flag to results
    try:
        cursor.execute("ALTER TABLE results ADD COLUMN cheated BOOLEAN DEFAULT 0")
        print("Added cheated column to results.")
    except sqlite3.OperationalError:
        pass

    # 3. Create password_resets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    cursor.execute('PRAGMA foreign_keys=on;')
    conn.close()
    print("Phase 3 Migration complete.")

if __name__ == '__main__':
    migrate()
