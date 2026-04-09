import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def seed_admin():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE email = 'admin@portal.com'")
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                       ('Administrator', 'admin@portal.com', hashed_password))
        conn.commit()
        print("Admin user created: admin@portal.com / admin123")
    else:
        print("Admin user already exists.")
        
    conn.close()

if __name__ == '__main__':
    seed_admin()
