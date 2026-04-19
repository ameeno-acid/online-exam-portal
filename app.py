from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def check_session():
    if 'user_id' in session and session.get('role') == 'student':
        if request.endpoint not in ['index', 'logout', 'login', 'static']:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT session_token FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            conn.close()
            if not user or user['session_token'] != session.get('session_token'):
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Session expired or logged in from another device', 'logout': True}), 401
                return redirect(url_for('index'))

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
        cursor.execute("INSERT INTO users (name, email, password_hash, role, status) VALUES (?, ?, ?, 'student', 'pending')", (name, email, hashed_password))
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
        if user['status'] == 'pending':
            return jsonify({'error': 'Account pending admin approval'}), 401
        if user['status'] == 'rejected':
            return jsonify({'error': 'Account rejected by admin'}), 401
            
        token = str(uuid.uuid4())
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (token, user['id']))
        conn.commit()
        conn.close()

        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        session['session_token'] = token
        
        target_board = 'admin' if user['role'] in ['admin', 'teacher'] else 'student'
        return jsonify({'success': 'Logged in successfully', 'redirect': url_for(f"{target_board}_dashboard")})
    
    return jsonify({'error': 'Invalid credentials or role mismatch'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': 'Logged out'})

def send_reset_email(to_email, token):
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    
    reset_link = request.host_url[:-1] + url_for('reset_password', token=token)

    if not email_user or not email_pass:
        print("\n=========================================")
        print("WARNING: EMAIL_USER and EMAIL_PASS not found in .env")
        print(f"[FALLBACK LOG] Password Reset Link: {reset_link}")
        print("=========================================\n")
        return False

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = to_email
    msg['Subject'] = "Password Reset Request - Online Exam Portal"
    
    body = f"""Hello,

You have requested to reset your password. Please click the strictly secure link below to set a new password:

{reset_link}

[SECURITY WARNING]: This link will expire in exactly 15 minutes. It is strictly valid for a single use only to protect your account.
If you did not request a password reset, please ignore this email and your password will remain unchanged.

Regards,
Online Exam Portal Security System
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("\n[DEBUG] Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print("[DEBUG] Logging in to SMTP server...")
        server.login(email_user, email_pass)
        print(f"[DEBUG] Sending email to {to_email}...")
        server.send_message(msg)
        server.quit()
        print("[DEBUG] Email sent successfully.")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email via SMTP: {e}")
        return False

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    print("\n[DEBUG] Forgot password route hit.")
    try:
        email = request.json.get('email')
        print(f"[DEBUG] Received email from request: {email}")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            print("[DEBUG] User exists in database.")
            token = str(uuid.uuid4())
            expires = datetime.now() + timedelta(minutes=15)
            
            print("[DEBUG] Generated token. Storing in database...")
            # Rather than deleting old tokens, mark them used or just let them expire. 
            # We'll just delete them to keep it clean or ignore them. We will stick to the single valid token approach:
            cursor.execute("DELETE FROM password_resets WHERE user_id = ?", (user['id'],))
            cursor.execute("INSERT INTO password_resets (token, user_id, expires_at, used) VALUES (?, ?, ?, 0)", 
                           (token, user['id'], expires))
            conn.commit()
            print("[DEBUG] Stored token successfully.")
            
            print("[DEBUG] Calling send_reset_email...")
            email_sent = send_reset_email(email, token)
            if not email_sent:
                print("[EMAIL ERROR] Could not deliver reset email.")
        else:
            print("[DEBUG] User does not exist, but returning generic positive response.")
            
        conn.close()
        return jsonify({'success': 'If your email exists, a secure reset link has been sent. Please check your inbox.'})
        
    except Exception as e:
        print(f"[ROUTE ERROR] /api/forgot-password failed: {e}")
        return jsonify({'error': 'An internal server error occurred while processing your request.'}), 500

@app.route('/reset-password/<token>')
def reset_password(token):
    print(f"\n[DEBUG] Reset password page hit with token: {token}")
    return render_template('reset_password.html', token=token)

@app.route('/api/reset-password', methods=['POST'])
def do_reset_password():
    print("\n[DEBUG] Reset password API hit.")
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            print("[TOKEN ERROR] Missing token or password in request.")
            return jsonify({'error': 'Missing fields'}), 400
            
        print(f"[DEBUG] Token received: {token}")
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, expires_at, used FROM password_resets WHERE token = ?", (token,))
        reset_entry = cursor.fetchone()
        
        if not reset_entry:
            conn.close()
            print("[TOKEN ERROR] Token not found in database.")
            return jsonify({'error': 'Invalid or expired token'}), 400
            
        if reset_entry['used'] == 1:
            conn.close()
            print("[TOKEN ERROR] Token has already been used.")
            return jsonify({'error': 'This token has already been used.'}), 400
            
        expires_at_str = reset_entry['expires_at'].split('.')[0]
        try:
            expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            expires_at = datetime.now() # Fallback if error
            
        if datetime.now() > expires_at:
            conn.close()
            print("[TOKEN ERROR] Token has expired.")
            return jsonify({'error': 'This reset token has expired. Please request a new one.'}), 400
            
        print("[DEBUG] Token validated successfully. Updating password...")
        hashed = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, reset_entry['user_id']))
        cursor.execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        
        print("[DEBUG] Password updated successfully.")
        return jsonify({'success': 'Password changed successfully. You may now login.'})
        
    except Exception as e:
        print(f"[DB ERROR] Error updating password: {e}")
        return jsonify({'error': 'An internal server error occurred while resetting your password.'}), 500

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') not in ['admin', 'teacher']:
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
    
    # Passing/Failing
    cursor.execute("SELECT COUNT(*) as count FROM results WHERE (score * 100.0 / total_questions) >= 50")
    passed = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM results WHERE (score * 100.0 / total_questions) < 50")
    failed = cursor.fetchone()['count']

    # Activity Logs
    cursor.execute('''
        SELECT al.*, u.name, e.exam_title 
        FROM activity_logs al
        JOIN users u ON al.student_id = u.id
        JOIN exams e ON al.exam_id = e.exam_id
        ORDER BY al.timestamp DESC LIMIT 10
    ''')
    activity_logs = cursor.fetchall()
    
    # Pending Users
    cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE status = 'pending' ORDER BY created_at DESC")
    pending_users = cursor.fetchall()

    conn.close()
    
    return render_template('admin_dashboard.html', 
                           name=session.get('name'),
                           role=session.get('role'),
                           total_students=total_students,
                           total_exams=total_exams,
                           recent_results=recent_results,
                           passed=passed,
                           failed=failed,
                           pending_users=pending_users,
                           activity_logs=activity_logs)

@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'approved' WHERE id = ?", (user_id,))
    
    # Also log this
    cursor.execute('''
        INSERT INTO activity_logs (student_id, exam_id, action_type, description)
        VALUES (?, 0, 'admin_approval', 'User approved by admin')
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'success': 'User approved'})

@app.route('/api/admin/users/<int:user_id>/reject', methods=['POST'])
def reject_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'rejected' WHERE id = ?", (user_id,))
    
    cursor.execute('''
        INSERT INTO activity_logs (student_id, exam_id, action_type, description)
        VALUES (?, 0, 'admin_rejection', 'User rejected by admin')
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'success': 'User rejected'})

@app.route('/admin/students')
def admin_students():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE role = 'student' ORDER BY created_at DESC")
    students = cursor.fetchall()
    conn.close()
    
    return render_template('admin_students.html', students=students)

@app.route('/api/admin/users/<int:student_id>', methods=['DELETE'])
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
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams ORDER BY created_at DESC")
    exams = cursor.fetchall()
    
    cursor.execute("SELECT * FROM subjects ORDER BY subject_name ASC")
    subjects = [row['subject_name'] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin_exams.html', exams=exams, subjects=subjects)

@app.route('/api/admin/subjects', methods=['POST'])
def create_subject():
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    subject_name = data.get('subject_name', '').strip()
    
    if not subject_name:
        return jsonify({'error': 'Subject name is required'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (subject_name,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Subject already exists'}), 400
        
    conn.close()
    return jsonify({'success': 'Subject added successfully'})

@app.route('/api/admin/subjects', methods=['DELETE'])
def delete_subject():
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json or {}
    subject_name = data.get('subject_name')
    if not subject_name:
        return jsonify({'error': 'Subject name required'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE subject_name = ?", (subject_name,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Subject deleted successfully'})

@app.route('/api/admin/exams', methods=['POST'])
def create_exam():
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    title = data.get('title')
    subject = data.get('subject')
    description = data.get('description', '')
    time_limit = data.get('time_limit')
    difficulty = data.get('difficulty', 'Medium')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not title or not subject or not time_limit or not start_date or not end_date:
        return jsonify({'error': 'Title, subject, time limit, and dates required'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO exams (exam_title, subject, description, difficulty, time_limit_minutes, start_date, end_date, created_by_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, subject, description, difficulty, time_limit, start_date, end_date, session.get('user_id'))
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Exam created'})

@app.route('/api/admin/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exams WHERE exam_id = ?", (exam_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Exam deleted'})

@app.route('/admin/exams/<int:exam_id>/questions')
def admin_questions(exam_id):
    if session.get('role') not in ['admin', 'teacher']:
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
    if session.get('role') not in ['admin', 'teacher']:
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
    if session.get('role') not in ['admin', 'teacher']:
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

@app.route('/admin/reopen_requests')
def admin_reopen_requests():
    if session.get('role') not in ['admin', 'teacher']:
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT req.*, u.name as student_name, e.exam_title,
               (SELECT cheated FROM results WHERE student_id = req.user_id AND exam_id = req.exam_id) as cheated
        FROM reopen_requests req
        JOIN users u ON req.user_id = u.id
        JOIN exams e ON req.exam_id = e.exam_id
        ORDER BY req.created_at ASC
    ''')
    reopen_requests = cursor.fetchall()
    conn.close()
    
    return render_template('admin_reopens.html', requests=reopen_requests)

@app.route('/api/admin/requests/<int:req_id>/approve', methods=['POST'])
def approve_request(req_id):
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json or {}
    granted_end_date = data.get('granted_end_date')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reopen_requests WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        return jsonify({'error': 'Request not found'}), 404
        
    cursor.execute("UPDATE reopen_requests SET status = 'approved', granted_end_date = ? WHERE id = ?", (granted_end_date, req_id))
    
    # Reset attempt
    cursor.execute("DELETE FROM results WHERE student_id = ? AND exam_id = ?", (req['user_id'], req['exam_id']))
    cursor.execute("DELETE FROM student_answers WHERE student_id = ? AND exam_id = ?", (req['user_id'], req['exam_id']))
    
    # Log it
    cursor.execute("INSERT INTO activity_logs (student_id, exam_id, action_type, description) VALUES (?, ?, 'reopen_approved', 'Exam reopened by admin')", (req['user_id'], req['exam_id']))
    
    conn.commit()
    conn.close()
    return jsonify({'success': 'Request approved'})

@app.route('/api/admin/requests/<int:req_id>/reject', methods=['POST'])
def reject_request(req_id):
    if session.get('role') not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE reopen_requests SET status = 'rejected' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': 'Request rejected'})

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('index'))
        
    student_id = session.get('user_id')
    conn = get_db()
    cursor = conn.cursor()
    
    # Attempted Exams (Results)
    cursor.execute('''
        SELECT r.*, e.exam_title, e.time_limit_minutes, e.difficulty
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
    
    cursor.execute("SELECT * FROM subjects ORDER BY subject_name ASC")
    subjects = [row['subject_name'] for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM reopen_requests WHERE user_id = ?", (student_id,))
    reopen_requests = {row['exam_id']: dict(row) for row in cursor.fetchall()}
    
    conn.close()
    
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    return render_template('student_dashboard.html', 
                           name=session.get('name'),
                           available_exams=available_exams,
                           attempted_exams=attempted_exams,
                           subjects=subjects,
                           reopen_requests=reopen_requests,
                           current_time=current_time)

@app.route('/api/student/requests/reopen', methods=['POST'])
def request_reopen():
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    exam_id = data.get('exam_id')
    reason = data.get('reason')
    description = data.get('description', '')
    
    if not exam_id or not reason:
        return jsonify({'error': 'Exam ID and reason are required'}), 400
        
    student_id = session.get('user_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if a pending or approved request already exists
    cursor.execute("SELECT status FROM reopen_requests WHERE user_id = ? AND exam_id = ?", (student_id, exam_id))
    existing = cursor.fetchone()
    if existing:
        if existing['status'] in ['pending', 'approved']:
            conn.close()
            return jsonify({'error': 'You already have an active request for this exam'}), 400
        else:
            # Overwrite rejected
            cursor.execute("UPDATE reopen_requests SET reason = ?, description = ?, status = 'pending', created_at = CURRENT_TIMESTAMP WHERE user_id = ? AND exam_id = ?",
                           (reason, description, student_id, exam_id))
    else:
        cursor.execute("INSERT INTO reopen_requests (user_id, exam_id, reason, description) VALUES (?, ?, ?, ?)",
                       (student_id, exam_id, reason, description))
                       
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Reopen request submitted successfully'})
@app.route('/student/exams/<int:exam_id>')
def student_exam(exam_id):
    if session.get('role') != 'student':
        return redirect(url_for('index'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exams WHERE exam_id = ?", (exam_id,))
    exam = cursor.fetchone()
    
    if not exam:
        conn.close()
        return redirect(url_for('student_dashboard'))
        
    student_id = session.get('user_id')
    
    # Check if already attempted
    cursor.execute("SELECT * FROM results WHERE student_id = ? AND exam_id = ?", (student_id, exam_id))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for('student_dashboard'))
        
    # Check time window OR approved reopen request
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    cursor.execute("SELECT * FROM reopen_requests WHERE user_id = ? AND exam_id = ? AND status = 'approved'", (student_id, exam_id))
    approved_req = cursor.fetchone()
    
    can_access = False
    
    if approved_req:
        # Ignore original window, rely on granted_end_date if exists, else it's open forever or original?
        # User said "Override endDate only for that specific student"
        if not approved_req['granted_end_date'] or approved_req['granted_end_date'] >= current_time:
            can_access = True
    else:
        # Use normal window
        if exam['start_date'] and current_time < exam['start_date']:
            can_access = False
        elif exam['end_date'] and current_time > exam['end_date']:
            can_access = False
        else:
            can_access = True
            
    if not can_access:
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

@app.route('/api/student/exams/<int:exam_id>/log_activity', methods=['POST'])
def log_activity(exam_id):
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    action_type = data.get('action')
    description = data.get('description', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activity_logs (student_id, exam_id, action_type, description)
        VALUES (?, ?, ?, ?)
    ''', (session.get('user_id'), exam_id, action_type, description))
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Activity logged'})

@app.route('/api/student/exams/<int:exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    if session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
        
    student_id = session.get('user_id')
    data = request.json
    answers = data.get('answers') # Expected: { question_id: 'A', ... }
    cheated = data.get('cheated', False)
    
    if answers is None:
        answers = {}
        
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
    
    if cheated:
        score = 0
    else:
        for q_id, selected_opt in answers.items():
            if correct_answers.get(str(q_id)) == selected_opt:
                score += 1
                
            cursor.execute('''
                INSERT INTO student_answers (student_id, exam_id, question_id, selected_option)
                VALUES (?, ?, ?, ?)
            ''', (student_id, exam_id, q_id, selected_opt))
            
    # Insert Result
    cursor.execute('''
        INSERT INTO results (student_id, exam_id, score, total_questions, cheated)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_id, exam_id, score, total_questions, cheated))
    
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
        SELECT r.*, e.exam_title, e.time_limit_minutes, e.difficulty
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
