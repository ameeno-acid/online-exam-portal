import os
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed_admin():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in .env!")
        return

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", ('admin@portal.com',))
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
                       ('Administrator', 'admin@portal.com', hashed_password))
        conn.commit()
        print("Admin user created: admin@portal.com / admin123")
    else:
        print("Admin user already exists.")
        
    conn.close()

if __name__ == '__main__':
    seed_admin()
