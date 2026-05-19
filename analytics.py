import csv
import datetime
from db_config import get_connection
from auth import log_audit

def fetch_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), ROUND(AVG(marks),2), MAX(marks), MIN(marks) FROM students")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def fetch_top_performers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department, marks FROM students ORDER BY marks DESC LIMIT 3")
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
            WHEN marks >= 90 THEN 'A'
            WHEN marks >= 75 THEN 'B'
            WHEN marks >= 60 THEN 'C'
            WHEN marks >= 40 THEN 'D'
            ELSE 'F'
        END AS grade,
        COUNT(*)
        FROM students
        GROUP BY grade
        ORDER BY grade
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_department_analytics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT department, ROUND(AVG(marks),2), MAX(marks), MIN(marks)
        FROM students
        GROUP BY department
        ORDER BY department
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_department_leaderboard():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT department, ROUND(AVG(marks),2) AS avg_marks
        FROM students
        GROUP BY department
        ORDER BY avg_marks DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def add_bonus_marks(department, bonus):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET marks = LEAST(marks + %s, 100) WHERE department = %s",
        (bonus, department)
    )
    conn.commit()
    cursor.close()
    conn.close()
    log_audit("BONUS_MARKS", f"Added {bonus} bonus marks to {department}")

def export_high_performers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, department, marks
        FROM students
        WHERE marks > (SELECT AVG(marks) FROM students)
        ORDER BY marks DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return None

    filename = f"high_performers_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Department", "Marks"])
        writer.writerows(rows)

    log_audit("EXPORT_CSV", f"Exported high performers to {filename}")
    return filename