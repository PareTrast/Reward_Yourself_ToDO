import flet as ft
import os
import sys
from supabase import create_async_client, AsyncClient
from user_storage import FileSystemUserStorage
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Conditional import based on environment
if "pyodide" in sys.modules:  # Running in a Pyodide (web) environment
    from pyodide.http import pyfetch  # type: ignore
else:  # Running in a non-web environment
    import requests

print("Running in web environment:", "pyodide" in sys.modules)


class UserManager:
    def __init__(self, page: ft.Page, users_dir="users"):
        self.page = page  # Store the page object for environment detection
        self.users_dir = users_dir
        self.user_storage = self.get_user_storage()
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.admin_supabase = None
        self.public_supabase = None
        print(f"Supabase Key: {self.supabase_key}")
        print(f"Running in web environment: {self.page.web}")

    def get_user_storage(self):
        return FileSystemUserStorage(self.users_dir)

    async def register_user(self, username, password):
        """
        Registers a new user with Supabase.
        """
        try:
            # Use pyfetch for HTTP requests in the web environment
            response = await pyfetch(
                url=f"{self.supabase_url}/auth/v1/signup",
                method="POST",
                headers={
                    "apikey": self.supabase_key,
                    "Content-Type": "application/json",
                },
                body=json.dumps(
                    {
                        "email": username,
                        "password": password,
                        "data": {"username": username},
                    }
                ),
            )
            data = await response.json()
            return (
                data.get("access_token"),
                data.get("user", {}).get("id"),
                data.get("refresh_token"),
            )
        except Exception as e:
            print(f"Error during registration (web): {e}")
            return None, None, None

    async def verify_user(self, email, password):
        """
        Verifies a user's credentials and logs them in.
        """
        try:
            response = await pyfetch(
                url=f"{self.supabase_url}/auth/v1/token?grant_type=password",
                method="POST",
                headers={
                    "apikey": self.supabase_key,
                    "Content-Type": "application/json",
                },
                body=json.dumps(
                    {
                        "email": email,
                        "password": password,
                    }
                ),
            )
            data = await response.json()
            return (
                data.get("access_token"),
                data.get("user", {}).get("id"),
                data.get("refresh_token"),
            )
        except Exception as e:
            print(f"Error during login (web): {e}")
            return None, None, None

    def get_access_token(self, username):
        return self.user_storage.get_access_token(username)

    async def get_supabase_client(self) -> AsyncClient:
        """Returns a Supabase client."""
        if self.public_supabase is None:
            self.public_supabase = await create_async_client(
                self.supabase_url, self.supabase_key
            )
        return self.public_supabase

    async def get_admin_supabase_client(self) -> AsyncClient:
        """Returns a Supabase client with service role key."""
        if self.admin_supabase is None:
            self.admin_supabase = await create_async_client(
                self.supabase_url, self.supabase_service_role_key
            )
        return self.admin_supabase
