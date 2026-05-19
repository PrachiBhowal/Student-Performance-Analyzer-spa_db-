from db_config import get_connection

def fetch_faculty_subjects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT faculty_username, subject_name, department, credits
        FROM vw_faculty_subjects
        ORDER BY faculty_username, subject_name
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_all_subject_marks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_name, department, subject_name, faculty_username, exam_type, marks, updated_at
        FROM vw_student_subject_marks
        ORDER BY student_name, subject_name
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_my_subject_marks(student_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sub.subject_name, u.username, ssm.exam_type, ssm.marks, ssm.updated_at
        FROM student_subject_marks ssm
        JOIN students st ON ssm.student_id = st.id
        JOIN subjects sub ON ssm.subject_id = sub.subject_id
        JOIN users u ON ssm.faculty_user_id = u.id
        WHERE st.user_id = %s
        ORDER BY sub.subject_name
    """, (student_user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_faculty_subject_marks(faculty_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT st.name, sub.subject_name, ssm.exam_type, ssm.marks, ssm.updated_at
        FROM student_subject_marks ssm
        JOIN students st ON ssm.student_id = st.id
        JOIN subjects sub ON ssm.subject_id = sub.subject_id
        WHERE ssm.faculty_user_id = %s
        ORDER BY st.name, sub.subject_name
    """, (faculty_user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows