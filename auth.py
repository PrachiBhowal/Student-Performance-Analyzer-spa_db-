import hashlib
from db_config import get_connection, current_user

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def login_user(username, password):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, username, role, is_active, password_hash
            FROM users
            WHERE username = %s
        """, (username,))
        user = cursor.fetchone()

        if not user:
            return False, "Invalid credentials or inactive account."

        if not user["is_active"]:
            return False, "Invalid credentials or inactive account."

        hashed = hash_password(password)
        if hashed != user["password_hash"]:
            return False, "Invalid credentials or inactive account."

        current_user["id"] = user["id"]
        current_user["username"] = user["username"]
        current_user["role"] = user["role"]
        return True, "Login successful"

    except Exception as e:
        return False, f"Login error: {e}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def logout_user():
    current_user["id"] = None
    current_user["username"] = None
    current_user["role"] = None

def log_audit(action, details):
    try:
        if not current_user.get("id"):
            return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, details)
            VALUES (%s, %s, %s)
        """, (current_user["id"], action, details))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass