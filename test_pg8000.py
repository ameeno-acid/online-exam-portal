import pg8000.dbapi
import os
from dotenv import load_dotenv

load_dotenv()

def test():
    db_url = os.environ.get('DATABASE_URL')
    
    # pg8000.dbapi.connect does not take a URL string directly by default, or maybe it does?
    # Let's check if it accepts kwargs
    db_url = db_url.replace("postgresql://", "").replace("postgres://", "")
    credentials, host_db = db_url.split("@")
    user, password = credentials.split(":")
    host, database = host_db.split("/")

    try:
        conn = pg8000.dbapi.connect(user=user, password=password, host=host, database=database)
        cursor = conn.cursor()
        
        # Test %s placeholder
        cursor.execute("SELECT * FROM users WHERE email = %s", ('admin@portal.com',))
        row = cursor.fetchone()
        print("Success! Row:", row)
        
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    test()
