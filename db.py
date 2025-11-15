# db.py
import mysql.connector
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'user': 'root',
    'password': 'Goutham@2002',
    'host': 'localhost',
    'database': 'student_details'
}

def get_connection(no_db=False):
    cfg = DB_CONFIG.copy()
    if no_db:
        cfg.pop('database', None)
    return mysql.connector.connect(**cfg)

def init_db():
    """Create database and tables."""
    try:
        conn = get_connection(no_db=True)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} DEFAULT CHARACTER SET 'utf8mb4'")
        cur.close()
        conn.close()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin','student') NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                batch_no VARCHAR(50),
                student_name VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                admin_name VARCHAR(100),
                trainer_name VARCHAR(100),
                suggestions TEXT,
                join_date DATE,
                course_combo VARCHAR(100),
                is_locked TINYINT(1) DEFAULT 0,
                edit_requested TINYINT(1) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS edit_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                requested_at DATETIME NOT NULL,
                status ENUM('pending','approved','rejected') DEFAULT 'pending',
                admin_id INT DEFAULT NULL,
                admin_comment TEXT,
                handled_at DATETIME DEFAULT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')

        # Default admin
        cur.execute("SELECT id FROM users WHERE username=%s", ('admin',))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO users (username, password, role) VALUES (%s,%s,'admin')",
                        ('admin', generate_password_hash('admin123')))

        conn.commit()
        cur.close()
        conn.close()
        print("Database and tables initialized successfully!")
    except mysql.connector.Error as e:
        print("DB error:", e)

# Small query helper for quick scripts if needed
def query_db(query, params=None, fetch=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, params or ())
    rows = None
    if fetch:
        rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return rows

if __name__ == '__main__':
    init_db()
