import datetime
from database import Database


class ToDoList:
    def __init__(self, username=None, is_web_environment=False):
        self.username = username
        self.user_id = None
        self.refresh_token = None
        self.access_token = None
        self.db = None
        self.is_web_environment = is_web_environment
        self.create_db_client()

    async def create_db_client(self):
        self.db = Database(self.is_web_environment)
        await self.db.create_supabase_client()
        if self.access_token and self.refresh_token:
            await self.db.set_access_token(self.access_token, self.refresh_token)

    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_refresh_token(self, refresh_token):
        self.refresh_token = refresh_token

    def set_access_token(self, access_token):
        self.access_token = access_token

    async def get_all_tasks(self):
        tasks = await self.db.get_tasks()
        return tasks

    async def get_all_rewards(self):
        rewards = await self.db.get_rewards()
        return rewards

    async def add_new_task(self, task_data):
        await self.db.add_task(task_data)

    async def add_new_reward(self, reward_data):
        await self.db.add_reward(reward_data)

    async def mark_task_done(self, task_id, task_name):
        history_data = {
            "username": self.username,
            "description": task_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": self.user_id,  # Add user_id here
        }
        await self.db.add_task_history(history_data, self.user_id)
        await self.db.delete_task(task_id)

    async def claim_reward(self, reward_id, reward_name):
        history_data = {
            "username": self.username,
            "description": reward_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "user_id": self.user_id,  # Add user_id here
        }
        await self.db.add_reward_history(history_data, self.user_id)
        await self.db.delete_reward(reward_id)

    async def get_task_history(self):
        return await self.db.get_task_history(self.user_id)

    async def get_reward_history(self):
        return await self.db.get_reward_history(self.user_id)
