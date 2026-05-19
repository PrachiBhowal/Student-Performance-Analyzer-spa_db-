import hashlib
from db_config import get_connection, current_user

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def print_table(headers, rows):
    if not rows:
        print("No records found.")
        return
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    line = "+".join("-" * (w + 2) for w in widths)
    print(line)
    print(" | ".join(str(headers[i]).ljust(widths[i]) for i in range(len(headers))))
    print(line)
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))
    print(line)

def log_audit(action, details=''):
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