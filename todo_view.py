import datetime
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print(f"Using API Key: {SUPABASE_KEY}")


class ToDoList:
    def __init__(self, username, is_web_environment):
        self.username = username
        self.is_web_environment = is_web_environment
        self.api_url = SUPABASE_URL + "/rest/v1"
        self.access_token = None
        self.user_id = None
        self.refresh_token = None
        self.db_client = None  # Add a placeholder for the database client

    async def create_db_client(self):
        """
        Initializes the database client.
        """
        try:
            from supabase import create_client

            self.db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Database client initialized successfully.")
        except Exception as e:
            print(f"Error initializing database client: {e}")

    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token

    def set_access_token(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

    async def get_all_tasks(self):
        """
        Fetches all tasks for the user.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/tasks?username=eq.{self.username}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching tasks: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching tasks: {e}")
            return []

    async def add_new_task(self, task_data):
        """
        Adds a new task for the user.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/tasks",
                    json=task_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                print("Task added successfully.")
        except httpx.HTTPStatusError as e:
            print(f"Error adding task: {e.response.text}")
        except Exception as e:
            print(f"Unexpected error adding task: {e}")

    async def get_all_rewards(self):
        """
        Fetches all rewards for the user.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "apikey": SUPABASE_KEY,
            }
            print(f"Headers: {headers}")  # Debugging
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/rewards?username=eq.{self.username}",
                    headers=headers,
                )
                response.raise_for_status()
                rewards = response.json()
                print(f"Fetched Rewards from API: {rewards}")  # Debugging
                return rewards
        except httpx.HTTPStatusError as e:
            print(f"Error fetching rewards: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching rewards: {e}")
            return []

    async def add_new_reward(self, reward_data):
        print(f"add_new_reward called with: {reward_data}")  # Debugging
        try:
            print(f"API URL: {self.api_url}/rewards")
            print(f"Reward Data: {reward_data}")
            print(f"API Key: {SUPABASE_KEY}")
            print(f"Access Token: {self.access_token}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/rewards",
                    json=reward_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                print("Reward added successfully.")
        except httpx.HTTPStatusError as e:
            print(f"Error adding reward: {e.response.text}")
        except Exception as e:
            print(f"Unexpected error adding reward: {e}")

    async def mark_task_done(self, task_id, task_name):
        """
        Marks a task as done and adds it to the task history.
        """
        history_data = {
            "username": self.username,
            "description": task_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": self.user_id,
        }
        try:
            async with httpx.AsyncClient() as client:
                # Add to task history
                response = await client.post(
                    f"{self.api_url}/task_history",
                    json=history_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                # Delete the task
                response = await client.delete(
                    f"{self.api_url}/tasks?id=eq.{task_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                print("Task marked as done successfully.")
        except httpx.HTTPStatusError as e:
            print(f"Error marking task as done: {e.response.text}")
        except Exception as e:
            print(f"Unexpected error marking task as done: {e}")

    async def claim_reward(self, reward_id, reward_name):
        """
        Claims a reward and adds it to the reward history.
        """
        history_data = {
            "username": self.username,
            "description": reward_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": self.user_id,
        }
        try:
            async with httpx.AsyncClient() as client:
                # Add to reward history
                response = await client.post(
                    f"{self.api_url}/reward_history",
                    json=history_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                # Delete the reward
                response = await client.delete(
                    f"{self.api_url}/rewards?id=eq.{reward_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                print(
                    f"Reward {reward_name} claimed and removed successfully."
                )  # Debugging
        except httpx.HTTPStatusError as e:
            print(f"Error claiming reward: {e.response.text}")
        except Exception as e:
            print(f"Unexpected error claiming reward: {e}")

    async def get_task_history(self):
        """
        Fetches the task history for the user.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/task_history?user_id=eq.{self.user_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching task history: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching task history: {e}")
            return []

    async def get_reward_history(self):
        """
        Fetches the reward history for the user.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/reward_history?user_id=eq.{self.user_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching reward history: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching reward history: {e}")
            return []
