import hashlib
import os


class UserManager:
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    def register_user(self, username, password):
        user_path = os.path.join(self.users_dir, username)
        if os.path.exists(user_path):
            return False
        os.makedirs(user_path, exist_ok=True)
        
        salt = os.urandom(16)
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        with open(user_path, "wb") as f:
            f.write(salt + hashed_password.encode())
        return True

    def verify_user(self, username, password):
        user_path = os.path.join(self.users_dir, username)
        if not os.path.exists(user_path):
            return False
        with open(user_path, "rb") as f:
            salt = f.read(16)
            stored_hash = f.read().decode()
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        return hashed_password == stored_hash
