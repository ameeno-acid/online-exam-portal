import os
import pg8000.native
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed_datasets():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in .env!")
        return

    # Parse URL: postgresql://user:password@host/database
    db_url = db_url.replace("postgresql://", "").replace("postgres://", "")
    credentials, host_db = db_url.split("@")
    user, password = credentials.split(":")
    host, database = host_db.split("/")

    try:
        conn = pg8000.native.Connection(user=user, password=password, host=host, database=database)
        
        # Get admin user ID
        admin_result = conn.run("SELECT id FROM users WHERE email = :email", email='admin@portal.com')
        if not admin_result:
            print("Admin user not found. Please run seed_admin_pg8000.py first.")
            return
        admin_id = admin_result[0][0]

        # Check if student exists
        student_result = conn.run("SELECT id FROM users WHERE email = :email", email='student@portal.com')
        if not student_result:
            hashed_password = generate_password_hash('student123')
            conn.run("INSERT INTO users (name, email, password_hash, role) VALUES (:name, :email, :password_hash, 'student')",
                        name='Test Student', email='student@portal.com', password_hash=hashed_password)
            print("Student user created: student@portal.com / student123")

        # Check if exams exist
        existing_exams = conn.run("SELECT exam_id FROM exams")
        if existing_exams:
            print("Exams already exist, skipping dataset seeding.")
        else:
            datasets = [
                {
                    "title": "Basic Physics Concepts",
                    "subject": "Physics",
                    "description": "Test your knowledge of fundamental physics concepts like kinematics and forces.",
                    "time_limit": 15,
                    "questions": [
                        {"text": "What is the SI unit of force?", "a": "Joule", "b": "Newton", "c": "Watt", "d": "Pascal", "correct": "B"},
                        {"text": "Which of the following is a scalar quantity?", "a": "Velocity", "b": "Acceleration", "c": "Speed", "d": "Force", "correct": "C"}
                    ]
                },
                {
                    "title": "Data Structures & Algorithms",
                    "subject": "Computer Science",
                    "description": "Assess your understanding of basic CS data structures.",
                    "time_limit": 20,
                    "questions": [
                        {"text": "Which data structure uses LIFO (Last In First Out)?", "a": "Queue", "b": "Stack", "c": "Tree", "d": "Graph", "correct": "B"}
                    ]
                }
            ]

            for exam in datasets:
                conn.run('''
                    INSERT INTO exams (exam_title, subject, description, total_questions, time_limit_minutes, created_by_admin)
                    VALUES (:title, :subject, :desc, :total, :limit, :admin)
                ''', title=exam['title'], subject=exam['subject'], desc=exam['description'], total=len(exam['questions']), limit=exam['time_limit'], admin=admin_id)
                
                # In pg8000, we need to query the last inserted ID
                exam_id_result = conn.run("SELECT exam_id FROM exams ORDER BY exam_id DESC LIMIT 1")
                exam_id = exam_id_result[0][0]
                
                for q in exam['questions']:
                    conn.run('''
                        INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
                        VALUES (:e_id, :qt, :oa, :ob, :oc, :od, :co)
                    ''', e_id=exam_id, qt=q['text'], oa=q['a'], ob=q['b'], oc=q['c'], od=q['d'], co=q['correct'])

            print("Seed datasets inserted successfully.")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    seed_datasets()
