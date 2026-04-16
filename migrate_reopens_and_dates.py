import sqlite3

DATABASE = 'database.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Checking exams table...")
    # Add start_date and end_date to exams
    try:
        cursor.execute("ALTER TABLE exams ADD COLUMN start_date TEXT")
        print("start_date column added to exams.")
    except sqlite3.OperationalError as e:
        # Expected if column already exists
        print(f"start_date: {e}")

    try:
        cursor.execute("ALTER TABLE exams ADD COLUMN end_date TEXT")
        print("end_date column added to exams.")
    except sqlite3.OperationalError as e:
        print(f"end_date: {e}")

    print("Creating reopen_requests table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reopen_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            granted_end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
        )
    ''')
    print("reopen_requests table verified/created.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
