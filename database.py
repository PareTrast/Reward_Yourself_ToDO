import os
import shutil
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class Storage:
    def create_tables(self):
        raise NotImplementedError

    def load_data(self):
        raise NotImplementedError

    def add_task(self, task, due_date=None):
        raise NotImplementedError

    def mark_task_done(self, task_id):
        raise NotImplementedError

    def add_reward(self, reward, medal_cost):
        raise NotImplementedError

    def claim_reward(self, reward_id):
        raise NotImplementedError

    def get_tasks(self, due_date=None):
        raise NotImplementedError

    def get_tasks_by_date_range(self, start_date, end_date):
        raise NotImplementedError

    def get_rewards(self):
        raise NotImplementedError

    def export_data(self, export_path):
        raise NotImplementedError

    def import_data(self, import_path):
        raise NotImplementedError


class SupabaseStorage(Storage):
    def __init__(self, api_url, api_key, username):
        self.supabase: Client = create_client(api_url, api_key)
        self.username = username
        self.data = {"tasks": [], "rewards": [], "medals": 0}
        self.medals = 0  # Initialize medals to 0
        self.load_data()

    def load_data(self):
        """
        Load tasks, rewards, and medals from Supabase.
        """
        # Load medals
        response = (
            self.supabase.table("medals")
            .select("count")
            .eq("username", self.username)
            .execute()
        )
        if response.data:
            self.data["medals"] = response.data[0]["count"]
            self.medals = self.data["medals"]  # Sync medals attribute
        else:
            # Initialize medals for the user if not present
            self.supabase.table("medals").insert(
                {"username": self.username, "count": 0}
            ).execute()
            self.data["medals"] = 0
            self.medals = 0

        # Load tasks
        response = (
            self.supabase.table("tasks")
            .select("*")
            .eq("username", self.username)
            .execute()
        )
        self.data["tasks"] = response.data if response.data else []

        # Load rewards
        response = (
            self.supabase.table("rewards")
            .select("*")
            .eq("username", self.username)
            .execute()
        )
        self.data["rewards"] = response.data if response.data else []

    def save_medals(self):
        """
        Save medals count to Supabase.
        """
        self.supabase.table("medals").update({"count": self.data["medals"]}).eq(
            "username", self.username
        ).execute()

    def add_task(self, task, due_date=None):
        """
        Add a new task to Supabase.
        """
        self.supabase.table("tasks").insert(
            {
                "username": self.username,
                "task": task,
                "done": False,
                "due_date": due_date,
            }
        ).execute()

    def mark_task_done(self, task_id):
        """
        Mark a task as done and increment medals count.
        """
        self.supabase.table("tasks").delete().eq("id", task_id).execute()
        self.data["medals"] += 1
        self.medals = self.data["medals"]  # Sync medals attribute
        self.save_medals()

    def add_reward(self, reward, medal_cost):
        """
        Add a new reward to Supabase.
        """
        self.supabase.table("rewards").insert(
            {"username": self.username, "reward": reward, "medal_cost": medal_cost}
        ).execute()

    def claim_reward(self, reward_id):
        """
        Claim a reward if the user has enough medals.
        """
        response = (
            self.supabase.table("rewards").select("*").eq("id", reward_id).execute()
        )
        if response.data:
            reward = response.data[0]
            if self.data["medals"] >= reward["medal_cost"]:
                self.data["medals"] -= reward["medal_cost"]
                self.medals = self.data["medals"]  # Sync medals attribute
                self.save_medals()
                self.supabase.table("rewards").delete().eq("id", reward_id).execute()
                return True
        return False

    def get_tasks(self, due_date=None):
        """
        Retrieve tasks from Supabase.
        """
        if due_date:
            response = (
                self.supabase.table("tasks")
                .select("*")
                .eq("username", self.username)
                .eq("due_date", due_date)
                .execute()
            )
        else:
            response = (
                self.supabase.table("tasks")
                .select("*")
                .eq("username", self.username)
                .execute()
            )
        return response.data

    def get_rewards(self):
        """
        Retrieve rewards from Supabase.
        """
        response = (
            self.supabase.table("rewards")
            .select("*")
            .eq("username", self.username)
            .execute()
        )
        return response.data  # Ensure this returns a list of dictionaries


def get_storage(page, username):
    """
    Factory function to initialize the appropriate storage backend.
    Uses Supabase for both web and non-web platforms.
    """
    print("Using Supabase for storage.")
    api_url = os.getenv("SUPABASE_API_URL")  # Use environment variables for security
    api_key = os.getenv("SUPABASE_API_KEY")
    if not api_url or not api_key:
        raise RuntimeError(
            "Supabase API URL or API Key is not set in environment variables."
        )
    return SupabaseStorage(api_url, api_key, username)
