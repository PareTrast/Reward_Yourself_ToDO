import hashlib
import os
import sqlite3


class UserManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt BLOB,
                password_hash TEXT
            )
        """)
        conn.commit()
        conn.close()

    def register_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            salt = os.urandom(16)
            hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt, hashed_password)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def verify_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
            
        salt, stored_hash = result
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        return hashed_password == stored_hash
