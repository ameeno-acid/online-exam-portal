import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

def approve_users():
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
        
        # Approve all current users
        conn.run("UPDATE users SET status = 'approved'")
        
        print("All users have been approved successfully!")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    approve_users()
