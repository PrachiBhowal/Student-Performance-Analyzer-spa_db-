from db_config import get_connection, current_user

def fetch_faculty_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.username AS faculty_username,
            sub.subject_name,
            sub.department,
            sub.credits
        FROM faculty_subjects fs
        JOIN users u ON fs.faculty_user_id = u.id
        JOIN subjects sub ON fs.subject_id = sub.subject_id
        ORDER BY u.username, sub.subject_name
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_all_subject_marks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.name AS student_name,
            s.department,
            sub.subject_name,
            fu.username AS faculty_username,
            ssm.exam_type,
            ssm.marks,
            ssm.updated_at
        FROM student_subject_marks ssm
        JOIN students s ON ssm.student_id = s.id
        JOIN subjects sub ON ssm.subject_id = sub.subject_id
        JOIN users fu ON ssm.faculty_user_id = fu.id
        ORDER BY s.name, sub.subject_name, ssm.exam_type
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_my_subject_marks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            sub.subject_name,
            fu.username AS faculty_username,
            ssm.exam_type,
            ssm.marks,
            ssm.updated_at
        FROM student_subject_marks ssm
        JOIN subjects sub ON ssm.subject_id = sub.subject_id
        JOIN users fu ON ssm.faculty_user_id = fu.id
        JOIN students s ON ssm.student_id = s.id
        WHERE s.user_id = %s
        ORDER BY sub.subject_name, ssm.exam_type
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def add_subject_mark(student_id, subject_id, faculty_user_id, exam_type, marks):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_subject_marks
        (student_id, subject_id, faculty_user_id, exam_type, marks)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, subject_id, faculty_user_id, exam_type, marks))
    conn.commit()
    cursor.close()
    conn.close()

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


def upsert_subject_mark(student_id, subject_id, faculty_user_id, exam_type, marks):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM student_subject_marks
        WHERE student_id = %s AND subject_id = %s AND exam_type = %s
    """, (student_id, subject_id, exam_type))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE student_subject_marks
            SET marks = %s, faculty_user_id = %s, updated_at = NOW()
            WHERE student_id = %s AND subject_id = %s AND exam_type = %s
        """, (marks, faculty_user_id, student_id, subject_id, exam_type))
    else:
        cursor.execute("""
            INSERT INTO student_subject_marks
            (student_id, subject_id, faculty_user_id, exam_type, marks)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, subject_id, faculty_user_id, exam_type, marks))

    conn.commit()
    cursor.close()
    conn.close()