import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "shona",
    "database": "spa_db"
}

current_user = {"id": None, "username": None, "role": None, "student_id": None}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)