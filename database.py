import pymysql
from fastapi import HTTPException

def init_db():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="mypassword"  # change it while implementing
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS registration")
    cursor.execute("USE registration")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(255) PRIMARY KEY,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()
    cursor.close()
    conn.close()


def get_user(username: str) -> dict | None:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="mypassword",     # change it while implementing
        database="registration",   # change it accordingly
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, hashed_password, full_name FROM users WHERE username = %s",
        (username,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "username": row["username"],
            "hashed_password": row["hashed_password"],
            "full_name": row["full_name"]
        }
    return None


def create_user(username: str, hashed_password: str, full_name: str = ""):
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="mypassword",   # change it while implementing
        database="registration"  # change it accordingly
    )
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password, full_name) VALUES (%s, %s, %s)",
            (username, hashed_password, full_name)
        )
        conn.commit()
    except pymysql.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")
    finally:
        cursor.close()
        conn.close() 