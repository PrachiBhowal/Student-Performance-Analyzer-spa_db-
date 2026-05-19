from db_config import get_connection
from auth import hash_password, log_audit

def fetch_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, is_active, created_at FROM users ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def create_user(username, password, role, student_name=None, department=None, marks=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, %s, %s)",
        (username, hash_password(password), role, True)
    )
    user_id = cursor.lastrowid

    if role == "student":
        cursor.execute(
            "INSERT INTO students (name, department, marks, user_id) VALUES (%s, %s, %s, %s)",
            (student_name, department, marks, user_id)
        )

    conn.commit()
    cursor.close()
    conn.close()
    log_audit("CREATE_USER", f"Created user {username} with role {role}")

def toggle_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = NOT is_active WHERE username = %s", (username,))
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("TOGGLE_USER", f"Toggled active status for {username}")

def create_mysql_users():
    conn = get_connection()
    cursor = conn.cursor()
    statements = [
        "DROP USER IF EXISTS 'spa_admin'@'localhost'",
        "DROP USER IF EXISTS 'spa_faculty'@'localhost'",
        "DROP USER IF EXISTS 'spa_student'@'localhost'",
        "CREATE USER 'spa_admin'@'localhost' IDENTIFIED BY 'Admin@123'",
        "CREATE USER 'spa_faculty'@'localhost' IDENTIFIED BY 'Faculty@123'",
        "CREATE USER 'spa_student'@'localhost' IDENTIFIED BY 'Student@123'",
        "GRANT ALL PRIVILEGES ON spa_db.* TO 'spa_admin'@'localhost'",
        "GRANT SELECT, INSERT, UPDATE ON spa_db.students TO 'spa_faculty'@'localhost'",
        "GRANT SELECT, INSERT ON spa_db.audit_log TO 'spa_faculty'@'localhost'",
        "GRANT SELECT ON spa_db.users TO 'spa_faculty'@'localhost'",
        "GRANT SELECT ON spa_db.students TO 'spa_student'@'localhost'",
        "GRANT SELECT, INSERT ON spa_db.audit_log TO 'spa_student'@'localhost'",
        "FLUSH PRIVILEGES"
    ]
    for stmt in statements:
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("CREATE_MYSQL_USERS", "Created MySQL application users")

def fetch_audit_log():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, action, details, timestamp
        FROM audit_log
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows