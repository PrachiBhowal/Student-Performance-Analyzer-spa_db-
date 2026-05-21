from db_config import get_connection
from auth import log_audit

def fetch_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("""
        SELECT ROUND(COALESCE(AVG(student_avg), 0), 2)
        FROM (
            SELECT s.id, AVG(ssm.marks) AS student_avg
            FROM students s
            LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
            GROUP BY s.id
        ) x
    """)
    avg_marks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT ROUND(COALESCE(MAX(student_total), 0), 2)
        FROM (
            SELECT s.id, COALESCE(SUM(ssm.marks), 0) AS student_total
            FROM students s
            LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
            GROUP BY s.id
        ) x
    """)
    highest = cursor.fetchone()[0]

    cursor.execute("""
        SELECT ROUND(COALESCE(MIN(student_total), 0), 2)
        FROM (
            SELECT s.id, COALESCE(SUM(ssm.marks), 0) AS student_total
            FROM students s
            LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
            GROUP BY s.id
        ) x
    """)
    lowest = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return total_students, avg_marks, highest, lowest

def fetch_top_performers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.department,
            ROUND(COALESCE(SUM(ssm.marks), 0), 2) AS total
        FROM students s
        LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
        GROUP BY s.id, s.name, s.department
        ORDER BY total DESC, s.name ASC
        LIMIT 3
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_marks_distribution():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            CASE
                WHEN marks >= 90 THEN 'A+'
                WHEN marks >= 80 THEN 'A'
                WHEN marks >= 70 THEN 'B'
                WHEN marks >= 60 THEN 'C'
                WHEN marks >= 50 THEN 'D'
                ELSE 'F'
            END AS grade,
            COUNT(*) AS count
        FROM student_subject_marks
        GROUP BY grade
        ORDER BY FIELD(grade, 'A+', 'A', 'B', 'C', 'D', 'F')
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_department_analytics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            dept.department,
            ROUND(AVG(dept.student_total), 2) AS avg_marks,
            ROUND(MAX(dept.student_total), 2) AS highest,
            ROUND(MIN(dept.student_total), 2) AS lowest
        FROM (
            SELECT s.id, s.department, COALESCE(SUM(ssm.marks), 0) AS student_total
            FROM students s
            LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
            GROUP BY s.id, s.department
        ) dept
        GROUP BY dept.department
        ORDER BY dept.department
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_department_leaderboard():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            dept.department,
            ROUND(AVG(dept.student_total), 2) AS avg_marks
        FROM (
            SELECT s.id, s.department, COALESCE(SUM(ssm.marks), 0) AS student_total
            FROM students s
            LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
            GROUP BY s.id, s.department
        ) dept
        GROUP BY dept.department
        ORDER BY avg_marks DESC, dept.department ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def add_bonus_marks(dept, bonus):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_subject_marks ssm
        JOIN students s ON ssm.student_id = s.id
        SET ssm.marks = LEAST(ssm.marks + %s, 100)
        WHERE s.department = %s
    """, (bonus, dept))
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("BONUS_MARKS", f"Added bonus marks {bonus} to department {dept}")

def export_high_performers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.department,
            ROUND(COALESCE(SUM(ssm.marks), 0), 2) AS total
        FROM students s
        LEFT JOIN student_subject_marks ssm ON s.id = ssm.student_id
        GROUP BY s.id, s.name, s.department
        HAVING total >= 250
        ORDER BY total DESC, s.name ASC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return None

    filename = "high_performers.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Department", "Total"])
        writer.writerows(rows)

    return filename