import os
import json
from supabase import create_async_client, AsyncClient
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


class Database:
    SESSION_FILE = "session.json"

    def __init__(self, is_web_environment=False):
        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is not set.")
        if not SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY environment variable is not set.")

        self.supabase: AsyncClient = None
        self.access_token = None
        self.refresh_token = None
        self.is_web_environment = is_web_environment

    async def create_supabase_client(self):
        self.supabase: AsyncClient = await create_async_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            options=ClientOptions(auto_refresh_token=True, persist_session=False),
        )

    async def set_access_token(self, access_token, refresh_token):

        self.access_token = access_token
        self.refresh_token = refresh_token

        await self.supabase.auth.set_session(access_token, refresh_token)

        self.save_session(access_token, refresh_token)

    def save_session(self, access_token, refresh_token):
        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        with open(self.SESSION_FILE, "w") as f:
            json.dump(session_data, f)

    def load_session(self):
        try:
            with open(self.SESSION_FILE, "r") as f:
                session_data = json.load(f)
                return session_data
        except FileNotFoundError:
            return None

    def _handle_response(self, response):
        if hasattr(response, "error") and response.error:
            raise Exception(f"Supabase error: {response.error}")
        return response.data

    async def get_tasks(self):
        try:
            response = await self.supabase.table("tasks").select("*").execute()
            return self._handle_response(response)
        except Exception as e:
            return []

    async def get_rewards(self):
        try:
            response = await self.supabase.table("rewards").select("*").execute()
            return self._handle_response(response)
        except Exception as e:
            return []

    async def add_task(self, task_data):
        try:
            response = await self.supabase.table("tasks").insert(task_data).execute()
            self._handle_response(response)
        except Exception as e:
            raise

    async def add_reward(self, reward_data):
        try:
            response = (
                await self.supabase.table("rewards").insert(reward_data).execute()
            )
            self._handle_response(response)
        except Exception as e:
            raise

    async def add_task_history(self, task_history_data, user_id):
        try:

            response = (
                await self.supabase.table("task_history")
                .insert(task_history_data)
                .execute()
            )
            self._handle_response(response)
        except Exception as e:
            raise

    async def add_reward_history(self, reward_history_data, user_id):
        try:

            response = (
                await self.supabase.table("reward_history")
                .insert(reward_history_data)
                .execute()
            )
            self._handle_response(response)
        except Exception as e:
            raise

    async def delete_task(self, task_id):
        try:
            response = (
                await self.supabase.table("tasks").delete().eq("id", task_id).execute()
            )
            self._handle_response(response)
        except Exception as e:
            raise

    async def delete_reward(self, reward_id):
        try:
            response = (
                await self.supabase.table("rewards")
                .delete()
                .eq("id", reward_id)
                .execute()
            )
            self._handle_response(response)
        except Exception as e:
            raise

    async def get_task_history(self, user_id):
        try:
            response = (
                await self.supabase.table("task_history")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching task history: {e}")
            return []

    async def get_reward_history(self, user_id):
        try:
            response = (
                await self.supabase.table("reward_history")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching reward history: {e}")
            return []
