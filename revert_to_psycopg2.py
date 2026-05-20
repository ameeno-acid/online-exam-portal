import os

APP_PY_PATH = 'app.py'
INIT_DB_PATH = 'init_db.py'
REQ_PATH = 'requirements.txt'

def revert_app_py():
    with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Revert psycopg3 back to psycopg2
    content = content.replace("import psycopg\nfrom psycopg.rows import dict_row", "import psycopg2\nimport psycopg2.extras")
    content = content.replace("import psycopg", "import psycopg2")
    
    old_wrapper = """class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor(row_factory=dict_row)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()"""
        
    new_wrapper = """class PostgresConnWrapper:
    def __init__(self, conn):
        self.conn = conn
    def cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()"""
        
    content = content.replace(old_wrapper, new_wrapper)
    content = content.replace("psycopg.IntegrityError", "psycopg2.IntegrityError")
    content = content.replace("psycopg.connect", "psycopg2.connect")
    
    with open(APP_PY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def revert_init_db():
    with open(INIT_DB_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace("import psycopg", "import psycopg2\nimport psycopg2.extras")
    content = content.replace("psycopg.connect", "psycopg2.connect")
    
    with open(INIT_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def revert_requirements():
    with open(REQ_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(REQ_PATH, 'w', encoding='utf-8') as f:
        for line in lines:
            if 'psycopg' not in line:
                f.write(line)
        f.write("psycopg2-binary==2.9.9\n")

if __name__ == '__main__':
    revert_app_py()
    revert_init_db()
    revert_requirements()
    print("Reverted to psycopg2-binary.")
