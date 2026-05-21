from db_config import get_connection, current_user
from auth import log_audit, hash_password


def fetch_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id,
            COALESCE(u.username, 'N/A') AS prn,
            s.name,
            s.department,
            ROUND(COALESCE(SUM(ssm.marks), 0), 2) AS total,
            ROUND(COALESCE(AVG(ssm.marks), 0), 2) AS average,
            s.enrolled_at
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
        GROUP BY s.id, u.username, s.name, s.department, s.enrolled_at
        ORDER BY s.id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def search_students_by_department(dept):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.department,
            ROUND(COALESCE(SUM(ssm.marks), 0), 2) AS total,
            ROUND(COALESCE(AVG(ssm.marks), 0), 2) AS average
        FROM students s
        LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
        WHERE s.department = %s
        GROUP BY s.id, s.name, s.department
        ORDER BY s.id
    """, (dept,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_own_record():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.department,
            ROUND(COALESCE(SUM(ssm.marks), 0), 2) AS total,
            ROUND(COALESCE(AVG(ssm.marks), 0), 2) AS average,
            s.enrolled_at
        FROM students s
        LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
        WHERE s.user_id = %s
        GROUP BY s.id, s.name, s.department, s.enrolled_at
    """, (current_user["id"],))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_all_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject_id, subject_name, department, credits
        FROM subjects
        ORDER BY subject_id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_student_subject_marks(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ssm.subject_id,
            sub.subject_name,
            ssm.exam_type,
            ssm.marks,
            ssm.updated_at
        FROM student_subject_marks ssm
        JOIN subjects sub ON ssm.subject_id = sub.subject_id
        WHERE ssm.student_id = %s
        ORDER BY sub.subject_name, ssm.exam_type
    """, (student_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def add_student(name, department, prn=None, password=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        user_id = None

        if prn and password:
            cursor.execute("SELECT id FROM users WHERE username = %s", (prn,))
            if cursor.fetchone():
                raise Exception("This PRN/username already exists.")

            cursor.execute("""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES (%s, %s, 'student', TRUE)
            """, (prn, hash_password(password)))
            user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO students (name, department, user_id)
            VALUES (%s, %s, %s)
        """, (name, department, user_id))

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


def update_student(student_id, field, value):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if field == "department":
            cursor.execute(
                "UPDATE students SET department = %s WHERE id = %s",
                (value, student_id)
            )
            log_audit("UPDATE_STUDENT", f"Updated department for student ID {student_id}")
        else:
            raise ValueError("Field must be department.")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def update_student_marks(student_id, subject_id, exam_type, marks, faculty_user_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM faculty_subjects
            WHERE faculty_user_id = %s AND subject_id = %s
        """, (faculty_user_id, subject_id))
        if not cursor.fetchone():
            raise Exception("You are not authorized to update marks for this subject.")

        cursor.execute("""
            INSERT INTO student_subject_marks
            (student_id, subject_id, faculty_user_id, exam_type, marks)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                faculty_user_id = VALUES(faculty_user_id),
                marks = VALUES(marks),
                updated_at = CURRENT_TIMESTAMP
        """, (student_id, subject_id, faculty_user_id, exam_type, marks))

        conn.commit()
        log_audit("UPDATE_MARKS", f"Updated marks for student {student_id}, subject {subject_id}, exam {exam_type}")
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


def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("DELETE_STUDENT", f"Deleted student ID {student_id}")