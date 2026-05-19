DROP DATABASE IF EXISTS spa_db;
CREATE DATABASE spa_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

USE spa_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL COLLATE utf8mb4_0900_ai_ci UNIQUE,
    password_hash CHAR(64) NOT NULL,
    role ENUM('admin', 'faculty', 'student') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL COLLATE utf8mb4_0900_ai_ci,
    marks DECIMAL(5,2) NOT NULL,
    user_id INT NULL UNIQUE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_marks CHECK (marks >= 0 AND marks <= 100),
    CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    details VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL COLLATE utf8mb4_0900_ai_ci,
    credits INT NOT NULL,
    CONSTRAINT chk_credits CHECK (credits > 0 AND credits <= 10)
);

CREATE TABLE faculty_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_user_id INT NOT NULL,
    subject_id INT NOT NULL,
    UNIQUE KEY uq_faculty_subject (faculty_user_id, subject_id),
    CONSTRAINT fk_faculty_subjects_user FOREIGN KEY (faculty_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_faculty_subjects_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
);

CREATE TABLE student_subject_marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    faculty_user_id INT NOT NULL,
    exam_type VARCHAR(50) NOT NULL,
    marks DECIMAL(5,2) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_subject_exam (student_id, subject_id, exam_type),
    CONSTRAINT chk_subject_marks CHECK (marks >= 0 AND marks <= 100),
    CONSTRAINT fk_ssm_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_ssm_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    CONSTRAINT fk_ssm_faculty FOREIGN KEY (faculty_user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT INTO users (username, password_hash, role, is_active) VALUES
('admin', SHA2('admin123', 256), 'admin', TRUE),
('faculty1', SHA2('faculty123', 256), 'faculty', TRUE),
('faculty2', SHA2('faculty123', 256), 'faculty', TRUE),
('faculty3', SHA2('faculty123', 256), 'faculty', TRUE),
('24070721001', SHA2('student123', 256), 'student', TRUE),
('24070721002', SHA2('student123', 256), 'student', TRUE),
('24070721003', SHA2('student123', 256), 'student', TRUE),
('24070721004', SHA2('student123', 256), 'student', TRUE),
('24070722001', SHA2('student123', 256), 'student', TRUE),
('24070722002', SHA2('student123', 256), 'student', TRUE),
('24070724003', SHA2('student123', 256), 'student', TRUE),
('24070724004', SHA2('student123', 256), 'student', TRUE);

INSERT INTO students (name, department, marks, user_id) VALUES
('Prachi Bhowal', 'CSE', 100.00, 5),
('Kalyan Bhowal', 'CSE', 94.00, 6),
('Riya Sen', 'CSE', 88.00, 7),
('Ankit Roy', 'CSE', 67.00, 8),
('Neha Das', 'CSE', 95.00, 9),
('Arjun Pal', 'CSE', 65.00, 10),
('Meera Ghosh', 'CSE', 82.00, 11),
('Khushi Chakrata', 'AIML', 97.00, 12),
('Dinesh Das', 'CST', 61.00, NULL),
('Krishna Iyer', 'CST', 82.00, NULL),
('Shreya Mittal', 'CSE', 85.00, NULL),
('Tanya Thakur', 'CST', 43.00, NULL);

INSERT INTO subjects (subject_name, department, credits) VALUES
('DBMS', 'CSE', 4),
('Operating Systems', 'CSE', 4),
('Python Programming', 'CSE', 3),
('Machine Learning', 'AIML', 4),
('Data Structures', 'CST', 4),
('Computer Networks', 'CST', 3);

INSERT INTO faculty_subjects (faculty_user_id, subject_id) VALUES
(2, 1),
(2, 2),
(3, 3),
(3, 5),
(4, 4),
(4, 6);

INSERT INTO student_subject_marks (student_id, subject_id, faculty_user_id, exam_type, marks) VALUES
(1, 1, 2, 'Midterm', 95.00),
(1, 2, 2, 'Midterm', 91.00),
(2, 1, 2, 'Midterm', 89.00),
(2, 2, 2, 'Midterm', 93.00),
(3, 3, 3, 'Midterm', 88.00),
(4, 3, 3, 'Midterm', 67.00),
(5, 4, 4, 'Midterm', 96.00),
(6, 5, 3, 'Midterm', 65.00),
(7, 1, 2, 'Midterm', 82.00),
(8, 4, 4, 'Midterm', 97.00),
(9, 5, 3, 'Midterm', 61.00),
(10, 6, 4, 'Midterm', 82.00),
(11, 1, 2, 'Midterm', 85.00),
(12, 6, 4, 'Midterm', 43.00);

CREATE OR REPLACE VIEW vw_faculty_subjects AS
SELECT
    u.username AS faculty_username,
    s.subject_name,
    s.department,
    s.credits
FROM faculty_subjects fs
JOIN users u ON fs.faculty_user_id = u.id
JOIN subjects s ON fs.subject_id = s.subject_id
ORDER BY u.username, s.subject_name;

CREATE OR REPLACE VIEW vw_student_subject_marks AS
SELECT
    st.name AS student_name,
    st.department,
    sub.subject_name,
    u.username AS faculty_username,
    ssm.exam_type,
    ssm.marks,
    ssm.updated_at
FROM student_subject_marks ssm
JOIN students st ON ssm.student_id = st.id
JOIN subjects sub ON ssm.subject_id = sub.subject_id
JOIN users u ON ssm.faculty_user_id = u.id
ORDER BY st.name, sub.subject_name, ssm.exam_type;

DROP USER IF EXISTS 'spa_admin'@'localhost';
DROP USER IF EXISTS 'spa_faculty'@'localhost';
DROP USER IF EXISTS 'spa_student'@'localhost';

CREATE USER 'spa_admin'@'localhost' IDENTIFIED BY 'admin123';
CREATE USER 'spa_faculty'@'localhost' IDENTIFIED BY 'faculty123';
CREATE USER 'spa_student'@'localhost' IDENTIFIED BY 'student123';

GRANT ALL PRIVILEGES ON spa_db.* TO 'spa_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE ON spa_db.students TO 'spa_faculty'@'localhost';
GRANT SELECT ON spa_db.users TO 'spa_faculty'@'localhost';
GRANT SELECT, INSERT ON spa_db.audit_log TO 'spa_faculty'@'localhost';
GRANT SELECT ON spa_db.subjects TO 'spa_faculty'@'localhost';
GRANT SELECT ON spa_db.faculty_subjects TO 'spa_faculty'@'localhost';
GRANT SELECT, INSERT, UPDATE ON spa_db.student_subject_marks TO 'spa_faculty'@'localhost';
GRANT SELECT ON spa_db.vw_faculty_subjects TO 'spa_faculty'@'localhost';
GRANT SELECT ON spa_db.vw_student_subject_marks TO 'spa_faculty'@'localhost';

GRANT SELECT ON spa_db.students TO 'spa_student'@'localhost';
GRANT SELECT ON spa_db.users TO 'spa_student'@'localhost';
GRANT INSERT ON spa_db.audit_log TO 'spa_student'@'localhost';
GRANT SELECT ON spa_db.subjects TO 'spa_student'@'localhost';
GRANT SELECT ON spa_db.student_subject_marks TO 'spa_student'@'localhost';
GRANT SELECT ON spa_db.vw_student_subject_marks TO 'spa_student'@'localhost';

FLUSH PRIVILEGES;