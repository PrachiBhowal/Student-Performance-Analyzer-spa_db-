from db_config import get_connection
from auth import hash_password, log_audit

def fetch_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, role, is_active, created_at
        FROM users
        ORDER BY id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def create_user(username, password, role, student_name=None, department=None, marks=None, student_id=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            raise Exception("Username already exists.")

        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (%s, %s, %s, TRUE)
        """, (username, hash_password(password), role))
        user_id = cursor.lastrowid

        linked_student_id = None

        if student_id:
            linked_student_id = student_id
        elif student_name and department:
            cursor.execute("""
                SELECT id
                FROM students
                WHERE name = %s AND department = %s AND user_id IS NULL
                ORDER BY id DESC
                LIMIT 1
            """, (student_name, department))
            row = cursor.fetchone()
            if row:
                linked_student_id = row[0]

        if linked_student_id:
            cursor.execute("""
                UPDATE students
                SET user_id = %s
                WHERE id = %s
            """, (user_id, linked_student_id))

        conn.commit()
        log_audit("CREATE_USER", f"Created user {username}")
        return user_id
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def toggle_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET is_active = NOT is_active
        WHERE username = %s
    """, (username,))
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("TOGGLE_USER", f"Toggled user {username}")


def create_mysql_users():
    conn = get_connection()
    cursor = conn.cursor()
    users = [
        ("spa_user", "localhost", "spa_pass123"),
        ("spa_admin", "localhost", "admin123"),
    ]
    db_name = "spa_db"

    try:
        for username, host, password in users:
            cursor.execute(
                f"CREATE USER IF NOT EXISTS '{username}'@'{host}' IDENTIFIED BY '{password}'"
            )
            cursor.execute(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON {db_name}.* TO '{username}'@'{host}'"
            )
        conn.commit()
        return True, "MySQL application users created successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def fetch_audit_log():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, action, details, timestamp
        FROM audit_log
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows