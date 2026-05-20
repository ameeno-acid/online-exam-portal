import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

def check_users():
    db_url = os.environ.get('DATABASE_URL')
    db_url = db_url.replace("postgresql://", "").replace("postgres://", "")
    credentials, host_db = db_url.split("@")
    user, password = credentials.split(":")
    host, database = host_db.split("/")

    try:
        conn = pg8000.native.Connection(user=user, password=password, host=host, database=database)
        
        users = conn.run("SELECT id, email, role FROM users")
        for u in users:
            print(u)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_users()
