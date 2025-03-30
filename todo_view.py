import platform
import os
import shutil
import flet as ft
from database import get_storage


class ToDoList:
    def __init__(self, page, username):
        self.storage = get_storage(page, username)  # Use the factory function
        self.load_data()

    def load_data(self):
        self.storage.load_data()
        self.medals = self.storage.medals  # This will now work correctly

    def add_task(self, task, due_date=None):
        self.storage.add_task(task, due_date)

    def mark_task_done(self, task_id):
        self.storage.mark_task_done(task_id)
        self.load_data()

    def add_reward(self, reward, medal_cost):
        self.storage.add_reward(reward, medal_cost)

    def claim_reward(self, reward_id):
        return self.storage.claim_reward(reward_id)

    def get_tasks(self, due_date=None):
        return self.storage.get_tasks(due_date)

    def get_tasks_by_date_range(self, start_date, end_date):
        return self.storage.get_tasks_by_date_range(start_date, end_date)

    def get_rewards(self):
        return self.storage.get_rewards()

    def export_data(self, export_path):
        self.storage.export_data(export_path)

    def import_data(self, import_path):
        self.storage.import_data(import_path)
