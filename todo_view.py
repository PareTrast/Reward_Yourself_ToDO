import datetime
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Conditional import based on environment
if "pyodide" in sys.modules:  # Running in a Pyodide (web) environment
    from pyodide.http import pyfetch  # type: ignore
else:  # Running in a non-web environment
    import requests


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
        if self.is_web_environment:
            # Web environment logic (if applicable)
            print("Web environment: No database client needed.")
        else:
            # Non-web environment logic
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

    def set_access_token(self, access_token):
        self.access_token = access_token

    async def get_all_tasks(self):
        """
        Fetches all tasks for the user.
        """
        try:
            response = await pyfetch(
                url=f"{SUPABASE_URL}/rest/v1/tasks?username=eq.{self.username}",
                method="GET",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json",
                },
            )
            tasks = await response.json()
            return tasks
        except Exception as e:
            print(f"Error fetching tasks (web): {e}")
            return []

    async def add_new_task(self, task_data):
        """
        Adds a new task for the user.
        """
        try:
            response = await pyfetch(
                url=f"{self.api_url}/tasks",
                method="POST",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Content-Type": "application/json",
                },
                body=json.dumps(task_data),
            )
            if response.status == 201:  # HTTP 201 Created
                print("Task added successfully.")
            else:
                print(f"Failed to add task. Status: {response.status}")
        except Exception as e:
            print(f"Error adding task (web): {e}")

    async def get_all_rewards(self):
        """
        Fetches all rewards for the user.
        """
        try:
            if self.is_web_environment:
                response = await pyfetch(
                    url=f"{self.api_url}/rewards?username=eq.{self.username}",
                    method="GET",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                return await response.json()
            else:
                response = requests.get(
                    f"{self.api_url}/rewards?username=eq.{self.username}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching rewards: {e}")
            return []

    async def add_new_reward(self, reward_data):
        """
        Adds a new reward for the user.
        """
        try:
            if self.is_web_environment:
                await pyfetch(
                    url=f"{self.api_url}/rewards",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                    body=reward_data,
                )
            else:
                response = requests.post(
                    f"{self.api_url}/rewards",
                    json=reward_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
        except Exception as e:
            print(f"Error adding reward: {e}")

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
            if self.is_web_environment:
                await pyfetch(
                    url=f"{self.api_url}/task_history",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                    body=history_data,
                )
                await pyfetch(
                    url=f"{self.api_url}/tasks?id=eq.{task_id}",
                    method="DELETE",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
            else:
                response = requests.post(
                    f"{self.api_url}/task_history",
                    json=history_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                response = requests.delete(
                    f"{self.api_url}/tasks?id=eq.{task_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
        except Exception as e:
            print(f"Error marking task as done: {e}")

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
            if self.is_web_environment:
                await pyfetch(
                    url=f"{self.api_url}/reward_history",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                    body=history_data,
                )
                await pyfetch(
                    url=f"{self.api_url}/rewards?id=eq.{reward_id}",
                    method="DELETE",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
            else:
                response = requests.post(
                    f"{self.api_url}/reward_history",
                    json=history_data,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                response = requests.delete(
                    f"{self.api_url}/rewards?id=eq.{reward_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
        except Exception as e:
            print(f"Error claiming reward: {e}")

    async def get_task_history(self):
        """
        Fetches the task history for the user.
        """
        try:
            if self.is_web_environment:
                response = await pyfetch(
                    url=f"{self.api_url}/task_history?user_id=eq.{self.user_id}",
                    method="GET",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                return await response.json()
            else:
                response = requests.get(
                    f"{self.api_url}/task_history?user_id=eq.{self.user_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching task history: {e}")
            return []

    async def get_reward_history(self):
        """
        Fetches the reward history for the user.
        """
        try:
            if self.is_web_environment:
                response = await pyfetch(
                    url=f"{self.api_url}/reward_history?user_id=eq.{self.user_id}",
                    method="GET",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                return await response.json()
            else:
                response = requests.get(
                    f"{self.api_url}/reward_history?user_id=eq.{self.user_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "apikey": SUPABASE_KEY,
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching reward history: {e}")
            return []
