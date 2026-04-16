import sqlite3

DATABASE = 'database.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    default_subjects = ['Physics', 'Chemistry', 'Computer Science', 'General']
    
    for sub in default_subjects:
        try:
            cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (sub,))
        except sqlite3.IntegrityError:
            pass # already exists
            
    # Also fetch any unique subjects that might somehow already exist in the exams table 
    # to avoid data integrity loss if the user played with it manually
    try:
        cursor.execute("SELECT DISTINCT subject FROM exams")
        existing_used = cursor.fetchall()
        for row in existing_used:
            try:
                cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (row['subject'],))
            except sqlite3.IntegrityError:
                pass
    except Exception:
        pass
        
    conn.commit()
    conn.close()
    print("Subjects Migration complete.")

if __name__ == '__main__':
    migrate()
