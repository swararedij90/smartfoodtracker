# db.py
import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Change if your MySQL has a password
        database="food_tracker_advanced"
    )
    return conn
