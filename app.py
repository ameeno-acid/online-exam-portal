from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = generate_password_hash(password)
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'student')", (name, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email already exists'}), 409
    
    conn.close()
    return jsonify({'success': 'Account created successfully'})

@app.route('/api/admin/register', methods=['POST'])
def register_admin():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'error': 'Missing fields'}), 400
        
    hashed_pw = generate_password_hash(password)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                       (name, email, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409
    finally:
        conn.close()
        
    return jsonify({'success': 'Registration successful'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role_type = data.get('role') # 'student' or 'admin'

    if not all([email, password, role_type]):
        return jsonify({'error': 'Missing credentials'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND role = ?", (email, role_type))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        return jsonify({'success': 'Logged in successfully', 'redirect': url_for(f"{user['role']}_dashboard")})
    
    return jsonify({'error': 'Invalid credentials or role mismatch'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': 'Logged out'})

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM exams")
    total_exams = cursor.fetchone()['count']
    
    cursor.execute('''
        SELECT r.*, u.name as student_name, e.exam_title 
        FROM results r 
        JOIN users u ON r.student_id = u.id 
        JOIN exams e ON r.exam_id = e.exam_id 
        ORDER BY r.submitted_at DESC LIMIT 5
    ''')
    recent_results = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           name=session.get('name'),
                           total_students=total_students,
                           total_exams=total_exams,
                           recent_results=recent_results)

@app.route('/admin/students')
def admin_students():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE role = 'student' ORDER BY created_at DESC")
    students = cursor.fetchall()
    conn.close()
    
    return render_template('admin_students.html', students=students)

@app.route('/api/admin/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ? AND role = 'student'", (student_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Student deleted successfully'})

@app.route('/admin/exams')
def admin_exams():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams ORDER BY created_at DESC")
    exams = cursor.fetchall()
    conn.close()
    
    return render_template('admin_exams.html', exams=exams)

@app.route('/api/admin/exams', methods=['POST'])
def create_exam():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    title = data.get('title')
    subject = data.get('subject')
    description = data.get('description', '')
    time_limit = data.get('time_limit')
    
    if not title or not subject or not time_limit:
        return jsonify({'error': 'Title, subject and time limit required'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO exams (exam_title, subject, description, time_limit_minutes, created_by_admin) VALUES (?, ?, ?, ?, ?)",
        (title, subject, description, time_limit, session.get('user_id'))
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Exam created'})

@app.route('/api/admin/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exams WHERE exam_id = ?", (exam_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Exam deleted'})

@app.route('/admin/exams/<int:exam_id>/questions')
def admin_questions(exam_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Get exam details
    cursor.execute("SELECT * FROM exams WHERE exam_id = ?", (exam_id,))
    exam = cursor.fetchone()
    if not exam:
        conn.close()
        return "Exam not found", 404
        
    # Get questions
    cursor.execute("SELECT * FROM questions WHERE exam_id = ?", (exam_id,))
    questions = cursor.fetchall()
    conn.close()
    
    return render_template('admin_questions.html', exam=exam, questions=questions)

@app.route('/api/admin/exams/<int:exam_id>/questions', methods=['POST'])
def add_question(exam_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    q_text = data.get('question_text')
    opt_a = data.get('option_a')
    opt_b = data.get('option_b')
    opt_c = data.get('option_c')
    opt_d = data.get('option_d')
    correct = data.get('correct_option')
    
    if not all([q_text, opt_a, opt_b, opt_c, opt_d, correct]) or correct not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'All fields required and correct option must be A, B, C, or D'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (exam_id, question_text, option_a, option_b, option_c, option_d, correct_option)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (exam_id, q_text, opt_a, opt_b, opt_c, opt_d, correct))
    
    # Update total questions count
    cursor.execute("UPDATE exams SET total_questions = total_questions + 1 WHERE exam_id = ?", (exam_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Question added'})

@app.route('/api/admin/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    
    # find exam_id to decrement count
    cursor.execute("SELECT exam_id FROM questions WHERE question_id = ?", (question_id,))
    row = cursor.fetchone()
    if row:
        exam_id = row['exam_id']
        cursor.execute("DELETE FROM questions WHERE question_id = ?", (question_id,))
        cursor.execute("UPDATE exams SET total_questions = total_questions - 1 WHERE exam_id = ?", (exam_id,))
        conn.commit()
        
    conn.close()
    return jsonify({'success': 'Question deleted'})

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('index'))
        
    student_id = session.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    
    # Attempted Exams (Results)
    cursor.execute('''
        SELECT r.*, e.exam_title, e.time_limit_minutes
        FROM results r
        JOIN exams e ON r.exam_id = e.exam_id
        WHERE r.student_id = ?
        ORDER BY r.submitted_at DESC
    ''', (student_id,))
    attempted_exams = cursor.fetchall()
    
    # Available Exams
    attempted_exam_ids = [row['exam_id'] for row in attempted_exams]
    
    if attempted_exam_ids:
        placeholders = ','.join(['?'] * len(attempted_exam_ids))
        cursor.execute(f'''
            SELECT * FROM exams 
            WHERE total_questions > 0 AND exam_id NOT IN ({placeholders})
            ORDER BY created_at DESC
        ''', attempted_exam_ids)
    else:
        cursor.execute("SELECT * FROM exams WHERE total_questions > 0 ORDER BY created_at DESC")
        
    available_exams = cursor.fetchall()
    
    conn.close()
    
    return render_template('student_dashboard.html', 
                           name=session.get('name'),
                           available_exams=available_exams,
                           attempted_exams=attempted_exams)

@app.route('/student/exams/<int:exam_id>')
def student_exam(exam_id):
    if session.get('role') != 'student':
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams WHERE exam_id = ?", (exam_id,))
    exam = cursor.fetchone()
    
    # Check if already attempted
    cursor.execute("SELECT * FROM results WHERE student_id = ? AND exam_id = ?", (session.get('user_id'), exam_id))
    if cursor.fetchone() or not exam:
        conn.close()
        return redirect(url_for('student_dashboard'))
        
    conn.close()
    return render_template('student_exam.html', exam=exam)

@app.route('/api/student/exams/<int:exam_id>/questions')
def get_exam_questions(exam_id):
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch random questions, omitting the correct_option
    cursor.execute('''
        SELECT question_id, question_text, option_a, option_b, option_c, option_d 
        FROM questions 
        WHERE exam_id = ? 
        ORDER BY RANDOM()
    ''', (exam_id,))
    
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'questions': questions})

@app.route('/api/student/exams/<int:exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    student_id = session.get('user_id')
    data = request.json
    answers = data.get('answers') # Expected: { question_id: 'A', ... }
    
    if not answers:
        return jsonify({'error': 'No answers submitted'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Ensure they haven't submitted already to prevent retakes
    cursor.execute("SELECT * FROM results WHERE student_id = ? AND exam_id = ?", (student_id, exam_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Exam already submitted'}), 403
        
    # Fetch correct options to grade
    cursor.execute("SELECT question_id, correct_option FROM questions WHERE exam_id = ?", (exam_id,))
    correct_answers = {str(row['question_id']): row['correct_option'] for row in cursor.fetchall()}
    
    score = 0
    total_questions = len(correct_answers)
    
    for q_id, selected_opt in answers.items():
        if correct_answers.get(str(q_id)) == selected_opt:
            score += 1
            
        cursor.execute('''
            INSERT INTO student_answers (student_id, exam_id, question_id, selected_option)
            VALUES (?, ?, ?, ?)
        ''', (student_id, exam_id, q_id, selected_opt))
        
    # Insert Result
    cursor.execute('''
        INSERT INTO results (student_id, exam_id, score, total_questions)
        VALUES (?, ?, ?, ?)
    ''', (student_id, exam_id, score, total_questions))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': 'Exam submitted successfully',
        'score': score,
        'total': total_questions
    })

@app.route('/student/results/<int:exam_id>')
def student_result(exam_id):
    if session.get('role') != 'student':
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch result
    cursor.execute('''
        SELECT r.*, e.exam_title, e.time_limit_minutes
        FROM results r
        JOIN exams e ON r.exam_id = e.exam_id
        WHERE r.student_id = ? AND r.exam_id = ?
    ''', (session.get('user_id'), exam_id))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return redirect(url_for('student_dashboard'))
        
    return render_template('student_result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
