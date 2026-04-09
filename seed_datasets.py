import sqlite3

DATABASE = 'database.db'

def seed_datasets():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get admin user ID (assuming admin@portal.com was created by seed_admin.py)
    cursor.execute("SELECT id FROM users WHERE email = 'admin@portal.com'")
    admin = cursor.fetchone()
    if not admin:
        print("Admin user not found. Please run seed_admin.py first.")
        return
    admin_id = admin[0]

    datasets = [
        {
            "title": "Basic Physics Concepts",
            "subject": "Physics",
            "description": "Test your knowledge of fundamental physics concepts like kinematics and forces.",
            "time_limit": 15,
            "questions": [
                {
                    "text": "What is the SI unit of force?",
                    "a": "Joule", "b": "Newton", "c": "Watt", "d": "Pascal",
                    "correct": "B"
                },
                {
                    "text": "Which of the following is a scalar quantity?",
                    "a": "Velocity", "b": "Acceleration", "c": "Speed", "d": "Force",
                    "correct": "C"
                }
            ]
        },
        {
            "title": "Introduction to Chemistry",
            "subject": "Chemistry",
            "description": "A beginner's quiz covering atomic structure and the periodic table.",
            "time_limit": 15,
            "questions": [
                {
                    "text": "What is the atomic number of Carbon?",
                    "a": "12", "b": "14", "c": "6", "d": "8",
                    "correct": "C"
                },
                {
                    "text": "Which element is a noble gas?",
                    "a": "Oxygen", "b": "Chlorine", "c": "Neon", "d": "Nitrogen",
                    "correct": "C"
                }
            ]
        },
        {
            "title": "Data Structures & Algorithms",
            "subject": "Computer Science",
            "description": "Assess your understanding of basic CS data structures.",
            "time_limit": 20,
            "questions": [
                {
                    "text": "Which data structure uses LIFO (Last In First Out)?",
                    "a": "Queue", "b": "Stack", "c": "Tree", "d": "Graph",
                    "correct": "B"
                },
                {
                    "text": "What is the worst-case time complexity of QuickSort?",
                    "a": "O(n log n)", "b": "O(n)", "c": "O(n^2)", "d": "O(1)",
                    "correct": "C"
                }
            ]
        }
    ]

    for exam in datasets:
        cursor.execute('''
            INSERT INTO exams (exam_title, subject, description, total_questions, time_limit_minutes, created_by_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (exam['title'], exam['subject'], exam['description'], len(exam['questions']), exam['time_limit'], admin_id))
        
        exam_id = cursor.lastrowid
        
        for q in exam['questions']:
            cursor.execute('''
                INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (exam_id, q['text'], q['a'], q['b'], q['c'], q['d'], q['correct']))

    conn.commit()
    conn.close()
    print("Seed datasets inserted successfully.")

if __name__ == '__main__':
    seed_datasets()
