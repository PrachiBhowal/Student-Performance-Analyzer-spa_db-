import hashlib
from db_config import get_connection, current_user

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_audit(action, details=""):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (user_id, action, details) VALUES (%s, %s, %s)",
            (current_user["id"], action, details)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

def login_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, role, is_active FROM users WHERE username = %s AND password_hash = %s",
            (username.strip(), hash_password(password.strip()))
        )
        user = cursor.fetchone()

        if user and user["is_active"]:
            current_user["id"] = user["id"]
            current_user["username"] = user["username"]
            current_user["role"] = user["role"]

            if user["role"] == "student":
                cursor.execute("SELECT id FROM students WHERE user_id = %s", (user["id"],))
                student = cursor.fetchone()
                current_user["student_id"] = student["id"] if student else None
            else:
                current_user["student_id"] = None

            log_audit("LOGIN_SUCCESS", f"{username} logged in successfully")
            cursor.close()
            conn.close()
            return True, f"Welcome, {user['username']}"
        else:
            log_audit("LOGIN_FAILED", f"Failed login for {username}")
            cursor.close()
            conn.close()
            return False, "Invalid credentials or inactive account."

    except Exception as e:
        return False, f"Login error: {e}"

def logout_user():
    log_audit("LOGOUT", f"{current_user['username']} logged out")
    current_user["id"] = None
    current_user["username"] = None
    current_user["role"] = None
    current_user["student_id"] = None