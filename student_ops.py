from db_config import get_connection, current_user
from auth import log_audit, hash_password

def fetch_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, u.username AS prn, s.name, s.department, s.marks, s.enrolled_at
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        ORDER BY s.id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def search_students_by_department(dept):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, department, marks FROM students WHERE department = %s ORDER BY id",
        (dept,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_own_record():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, department, marks, enrolled_at FROM students WHERE user_id = %s",
        (current_user["id"],)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def add_student(name, department, marks, prn=None, password=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        user_id = None

        if prn and password:
            hashed = hash_password(password)

            cursor.execute("SELECT id FROM users WHERE username = %s", (prn,))
            existing_user = cursor.fetchone()
            if existing_user:
                raise Exception("This PRN/username already exists.")

            cursor.execute("""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES (%s, %s, 'student', TRUE)
            """, (prn, hashed))
            user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO students (name, department, marks, user_id)
            VALUES (%s, %s, %s, %s)
        """, (name, department, marks, user_id))

        conn.commit()
        log_audit("INSERT_STUDENT", f"Added student {name}")
        return True

    except Exception:
        if conn:
            conn.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def update_student(student_identifier, field, value):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT s.id
            FROM students s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.id = %s OR u.username = %s
        """, (student_identifier, str(student_identifier)))

        row = cursor.fetchone()
        if not row:
            raise Exception(f"No student found with ID/PRN {student_identifier}.")

        student_id = row[0]

        if field == "marks":
            cursor.execute(
                "UPDATE students SET marks = %s WHERE id = %s",
                (value, student_id)
            )

        elif field == "department":
            cursor.execute(
                "UPDATE students SET department = %s WHERE id = %s",
                (value, student_id)
            )

        else:
            raise ValueError("Field must be either marks or department.")

        conn.commit()
        log_audit("UPDATE_STUDENT", f"Updated {field} for student ID {student_id}")

    except:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("DELETE_STUDENT", f"Deleted student ID {student_id}")