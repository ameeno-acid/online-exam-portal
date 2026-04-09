import sqlite3
import os

DATABASE = 'database.db'

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            total_questions INTEGER NOT NULL DEFAULT 0,
            time_limit_minutes INTEGER NOT NULL,
            created_by_admin INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_admin) REFERENCES users(id)
        )
    ''')

    # Create questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
        )
    ''')

    # Create student_answers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option TEXT CHECK(selected_option IN ('A', 'B', 'C', 'D')),
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
        )
    ''')

    # Create results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
