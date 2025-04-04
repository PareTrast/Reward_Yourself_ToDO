import flet as ft
import os
from supabase import create_async_client, AsyncClient
from user_storage import FileSystemUserStorage
from dotenv import load_dotenv

load_dotenv()


class UserManager:
    def __init__(self, page: ft.Page, users_dir="users"):
        self.page = page
        self.users_dir = users_dir
        self.user_storage = self.get_user_storage()
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.admin_supabase = None
        self.public_supabase = None

    def get_user_storage(self):
        return FileSystemUserStorage(self.users_dir)

    async def register_user(self, username, password):
        success, access_token, refresh_token, user_id = (
            await self.user_storage.register_user(
                username,
                password,
                await self.get_admin_supabase_client(),
            )
        )
        if success:
            return access_token, user_id, refresh_token
        else:
            return None, None, None

    async def verify_user(self, username, password):
        access_token, refresh_token, user_id = await self.user_storage.verify_user(
            username, password
        )
        if access_token:
            print(f"verify_user - access_token: {access_token}, user_id: {user_id}")
            return access_token, user_id, refresh_token
        else:
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
