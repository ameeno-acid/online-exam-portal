import os
import pg8000.native
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def seed_admin():
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
        
        # Check if admin already exists
        result = conn.run("SELECT * FROM users WHERE email = :email", email='admin@portal.com')
        if not result:
            hashed_password = generate_password_hash('admin123')
            conn.run("INSERT INTO users (name, email, password_hash, role) VALUES (:name, :email, :password_hash, 'admin')",
                        name='Administrator', email='admin@portal.com', password_hash=hashed_password)
            print("Admin user created: admin@portal.com / admin123")
        else:
            print("Admin user already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")

if __name__ == '__main__':
    seed_admin()
