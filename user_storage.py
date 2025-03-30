import os
import hashlib
import json
import flet as ft

class UserStorage:
    def register_user(self, username, password):
        raise NotImplementedError

    def verify_user(self, username, password):
        raise NotImplementedError

class FileSystemUserStorage(UserStorage):
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    def register_user(self, username, password):
        user_dir = os.path.join(self.users_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        user_path = os.path.join(user_dir, "password.txt")
        if os.path.exists(user_path):
            return False

        salt = os.urandom(16)
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        try:
            with open(user_path, "wb") as f:
                f.write(salt + hashed_password.encode())
            return True
        except OSError as e:
            print(f"Error registering user: {e}")
            return False

    def verify_user(self, username, password):
        user_dir = os.path.join(self.users_dir, username)
        user_path = os.path.join(user_dir, "password.txt")
        if not os.path.exists(user_path):
            return False

        try:
            with open(user_path, "rb") as f:
                salt = f.read(16)
                stored_hash = f.read().decode()
            hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
            return hashed_password == stored_hash
        except OSError as e:
            print(f"Error verifying user: {e}")
            return False

class LocalStorageUserStorage(UserStorage):
    def __init__(self, page: ft.Page, users_key="users"):
        self.page = page
        self.users_key = users_key
        self.load_users()

    def load_users(self):
        users_data = self.page.client_storage.get(self.users_key)
        if users_data:
            self.users = json.loads(users_data)
        else:
            self.users = {}

    def save_users(self):
        self.page.client_storage.set(self.users_key, json.dumps(self.users))

    def register_user(self, username, password):
        if username in self.users:
            return False
        salt = os.urandom(16).hex()  # Store salt as hex string
        hashed_password = hashlib.sha256((salt + password).encode()).hexdigest()
        self.users[username] = {"salt": salt, "hashed_password": hashed_password}
        self.save_users()
        return True

    def verify_user(self, username, password):
        if username not in self.users:
            return False
        salt = self.users[username]["salt"]
        stored_hash = self.users[username]["hashed_password"]
        hashed_password = hashlib.sha256((salt + password).encode()).hexdigest()
        return hashed_password == stored_hash