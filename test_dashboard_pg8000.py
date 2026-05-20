import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

def test_dashboard():
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
        
        student_id = 1  # Using 1 assuming student or admin exists

        # Query 1
        print("Running Query 1...")
        conn.run('''
            SELECT r.*, e.exam_title, e.time_limit_minutes, e.difficulty
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            WHERE r.student_id = :student_id
            ORDER BY r.submitted_at DESC
        ''', student_id=student_id)

        # Query 2
        print("Running Query 2...")
        conn.run("SELECT * FROM exams WHERE total_questions > 0 ORDER BY created_at DESC")

        # Query 3
        print("Running Query 3...")
        conn.run("SELECT * FROM subjects ORDER BY subject_name ASC")

        # Query 4
        print("Running Query 4...")
        conn.run("SELECT * FROM reopen_requests WHERE user_id = :student_id", student_id=student_id)

        print("All queries ran successfully.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_dashboard()
