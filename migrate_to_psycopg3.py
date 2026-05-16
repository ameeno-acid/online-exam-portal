import os

APP_PY_PATH = 'app.py'
INIT_DB_PATH = 'init_db.py'
REQ_PATH = 'requirements.txt'

def migrate_app_py():
    with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Replace psycopg2 imports
    content = content.replace("import psycopg2\nimport psycopg2.extras", "import psycopg\nfrom psycopg.rows import dict_row")
    content = content.replace("import psycopg2", "import psycopg")
    
    # 2. Update PostgresConnWrapper
    old_wrapper = """class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()"""
        
    new_wrapper = """class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor(row_factory=dict_row)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()"""
        
    content = content.replace(old_wrapper, new_wrapper)
    
    # 3. Replace psycopg2 with psycopg generally (like IntegrityError)
    content = content.replace("psycopg2.IntegrityError", "psycopg.IntegrityError")
    
    # 4. In psycopg v3, psycopg2.connect() is psycopg.connect()
    content = content.replace("psycopg2.connect", "psycopg.connect")
    
    with open(APP_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def migrate_init_db():
    with open(INIT_DB_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("import psycopg2\nimport psycopg2.extras", "import psycopg")
    content = content.replace("import psycopg2", "import psycopg")
    content = content.replace("psycopg2.connect", "psycopg.connect")
    
    with open(INIT_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def migrate_requirements():
    with open(REQ_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(REQ_PATH, 'w', encoding='utf-8') as f:
        for line in lines:
            if 'psycopg2' not in line:
                f.write(line)
        f.write("psycopg==3.1.18\n") # Or whatever current version is

if __name__ == '__main__':
    migrate_app_py()
    migrate_init_db()
    migrate_requirements()
    print("Migration to psycopg (v3) completed.")
