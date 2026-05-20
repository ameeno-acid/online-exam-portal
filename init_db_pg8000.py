import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

def init_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found!")
        return

    # Parse URL
    db_url = db_url.replace("postgresql://", "").replace("postgres://", "")
    credentials, host_db = db_url.split("@")
    user, password = credentials.split(":")
    host, database = host_db.split("/")

    try:
        conn = pg8000.native.Connection(user=user, password=password, host=host, database=database)
        
        queries = [
            '''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
                session_token TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS subjects (
                subject_id SERIAL PRIMARY KEY,
                subject_name TEXT UNIQUE NOT NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS exams (
                exam_id SERIAL PRIMARY KEY,
                exam_title TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                difficulty TEXT DEFAULT 'Medium',
                total_questions INTEGER NOT NULL DEFAULT 0,
                time_limit_minutes INTEGER NOT NULL,
                start_date TEXT,
                end_date TEXT,
                created_by_admin INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by_admin) REFERENCES users(id)
            )''',
            '''CREATE TABLE IF NOT EXISTS questions (
                question_id SERIAL PRIMARY KEY,
                exam_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS student_answers (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                selected_option TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS results (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                cheated INTEGER DEFAULT 0,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS activity_logs (
                log_id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS reopen_requests (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                granted_end_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
            )'''
        ]
        
        for q in queries:
            conn.run(q)
            
        print("All tables checked/created.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    init_db()
