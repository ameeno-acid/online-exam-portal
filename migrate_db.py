import sqlite3

DATABASE = 'database.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # Add session_token to users if it doesn't exist
        cursor.execute("ALTER TABLE users ADD COLUMN session_token TEXT")
        print("Added session_token to users table.")
    except sqlite3.OperationalError:
        print("session_token column might already exist.")

    try:
        # Add difficulty to exams if it doesn't exist
        cursor.execute("ALTER TABLE exams ADD COLUMN difficulty TEXT DEFAULT 'Medium'")
        print("Added difficulty to exams table.")
    except sqlite3.OperationalError:
        print("difficulty column might already exist.")

    # Create activity_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
        )
    ''')
    print("Checked/created activity_logs table.")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
