import os
from flask import Flask, session, render_template
import pg8000.dbapi
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = 'test'

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    db_url = db_url.replace("postgresql://", "").replace("postgres://", "")
    credentials, host_db = db_url.split("@")
    user, password = credentials.split(":")
    host, database = host_db.split("/")
    # pg8000.dbapi requires paramstyle='format' to support %s
    return pg8000.dbapi.connect(user=user, password=password, host=host, database=database)

@app.route('/test')
def test_dash():
    try:
        student_id = 1
        conn = get_db()
        cursor = conn.cursor()
        
        # We need a dict factory for pg8000 to mimic DictCursor
        def dictfetchall(cursor):
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT r.*, e.exam_title, e.time_limit_minutes, e.difficulty
            FROM results r
            JOIN exams e ON r.exam_id = e.exam_id
            WHERE r.student_id = %s
            ORDER BY r.submitted_at DESC
        ''', (student_id,))
        attempted_exams = dictfetchall(cursor)
        
        attempted_exam_ids = [row['exam_id'] for row in attempted_exams]
        
        if attempted_exam_ids:
            placeholders = ','.join(['%s'] * len(attempted_exam_ids))
            cursor.execute(f'''
                SELECT * FROM exams 
                WHERE total_questions > 0 AND exam_id NOT IN ({placeholders})
                ORDER BY created_at DESC
            ''', attempted_exam_ids)
        else:
            cursor.execute("SELECT * FROM exams WHERE total_questions > 0 ORDER BY created_at DESC")
            
        available_exams = dictfetchall(cursor)
        
        cursor.execute("SELECT * FROM subjects ORDER BY subject_name ASC")
        subjects = [row['subject_name'] for row in dictfetchall(cursor)]

        cursor.execute("SELECT * FROM reopen_requests WHERE user_id = %s", (student_id,))
        reopen_requests = {row['exam_id']: row for row in dictfetchall(cursor)}
        
        conn.close()
        
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
        
        return render_template('student_dashboard.html', 
                               name="Test",
                               available_exams=available_exams,
                               attempted_exams=attempted_exams,
                               subjects=subjects,
                               reopen_requests=reopen_requests,
                               current_time=current_time)
    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>"

if __name__ == '__main__':
    # Run the test server on port 5001 to avoid conflicts
    print("Test server running on http://127.0.0.1:5001/test")
    app.run(port=5001)
