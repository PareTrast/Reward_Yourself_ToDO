import flet as ft
from user_storage import FileSystemUserStorage, LocalStorageUserStorage

class UserManager:
    def __init__(self, page: ft.Page, users_dir="users"):
        if page.platform in ["android", "ios", "linux", "windows", "macos"]:
            self.user_storage = FileSystemUserStorage(users_dir)
        else:
            self.user_storage = LocalStorageUserStorage(page)

    def register_user(self, username, password):
        return self.user_storage.register_user(username, password)

    def verify_user(self, username, password):
        return self.user_storage.verify_user(username, password)

'''import hashlib
import os


class UserManager:
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    def register_user(self, username, password):
        user_path = os.path.join(self.users_dir, f"{username}.txt")
        if os.path.exists(user_path):
            return False
        
        salt = os.urandom(16)
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        with open(user_path, "wb") as f:
            f.write(salt + hashed_password.encode())
        return True

    def verify_user(self, username, password):
        user_path = os.path.join(self.users_dir, f"{username}.txt")
        if not os.path.exists(user_path):
            return False
        with open(user_path, "rb") as f:
            salt = f.read(16)
            stored_hash = f.read().decode()
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        return hashed_password == stored_hash
'''