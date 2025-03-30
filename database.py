import os
import shutil
import flet as ft
import json
import asyncio  # For non-blocking delays

# import js  # Pyodide's JavaScript interop module


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


class SQLiteStorage(Storage):
    def __init__(self, username):
        import sqlite3

        print("Sqlite imported")
        db_filename = f"{username}_todo.db"
        self.db_path = os.path.join("users", username, db_filename)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                done INTEGER,
                due_date TEXT NULL
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reward TEXT,
                medal_cost INTEGER
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS medals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count INTEGER
            )
        """
        )
        self.cursor.execute("INSERT OR IGNORE INTO medals (count) VALUES (0)")
        self.conn.commit()

    def load_data(self):
        self.cursor.execute("SELECT count FROM medals LIMIT 1")
        result = self.cursor.fetchone()
        self.medals = result[0] if result else 0  # Ensure medals is always defined

    def add_task(self, task, due_date=None):
        due_date = due_date or None
        self.cursor.execute(
            "INSERT INTO tasks (task, done, due_date) VALUES (?, ?, ?)",
            (task, 0, due_date),
        )
        self.conn.commit()

    def mark_task_done(self, task_id):
        self.cursor.execute("UPDATE medals SET count = count + 1")
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_data()

    def add_reward(self, reward, medal_cost):
        self.cursor.execute(
            "INSERT INTO rewards (reward, medal_cost) VALUES (?, ?)",
            (reward, medal_cost),
        )
        self.conn.commit()

    def claim_reward(self, reward_id):
        self.cursor.execute(
            "SELECT reward, medal_cost FROM rewards WHERE id = ?", (reward_id,)
        )
        result = self.cursor.fetchone()
        if result:
            reward, medal_cost = result
            if self.medals >= medal_cost:
                self.cursor.execute(
                    "UPDATE medals SET count = count - ?", (medal_cost,)
                )
                self.cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
                self.conn.commit()
                self.load_data()
                return True
            else:
                return False
        else:
            return None

    def get_tasks(self, due_date=None):
        if due_date:
            self.cursor.execute(
                "SELECT id, task, done, due_date FROM tasks WHERE due_date = ?",
                (due_date,),
            )
        else:
            self.cursor.execute("SELECT id, task, done, due_date FROM tasks")
        # Ensure all rows include 4 values (id, task, done, due_date)
        return [
            (row[0], row[1], row[2], row[3] if row[3] else None)
            for row in self.cursor.fetchall()
        ]

    def get_tasks_by_date_range(self, start_date, end_date):
        self.cursor.execute(
            "SELECT id, task, done, due_date FROM tasks WHERE due_date BETWEEN ? AND ?",
            (start_date, end_date),
        )
        return self.cursor.fetchall()

    def get_rewards(self):
        self.cursor.execute("SELECT id, reward, medal_cost FROM rewards")
        return self.cursor.fetchall()

    def export_data(self, export_path):
        shutil.copy(self.db_path, export_path)

    def import_data(self, import_path):
        shutil.copy(import_path, self.db_path)
        self.load_data()

    def close(self):
        self.conn.close()


class LocalStorage(Storage):
    def __init__(self, page: ft.Page, username):
        self.page = page
        self.username = username
        self.data = {"tasks": [], "rewards": [], "medals": 0}
        self.medals = 0  # Initialize medals to 0

    async def load_data(self):
        """
        Load data from the browser's localStorage.
        """
        if not self.page.web:
            print("Error: Attempted to use LocalStorage in a non-web environment.")
            return

        try:
            # Import js only when needed
            import js

            # Access localStorage using Pyodide's js module
            data = js.window.localStorage.getItem(self.username)
            if data:
                self.data = json.loads(data)
            else:
                self.data = {"tasks": [], "rewards": [], "medals": 0}
            self.medals = self.data["medals"]
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = {"tasks": [], "rewards": [], "medals": 0}

    def save_data(self):
        """
        Save data to the browser's localStorage.
        """
        if not self.page.web:
            print("Error: Attempted to use LocalStorage in a non-web environment.")
            return

        try:
            # Import js only when needed
            import js

            # Save data to localStorage using Pyodide's js module
            js.window.localStorage.setItem(self.username, json.dumps(self.data))
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_task(self, task, due_date=None):
        self.data["tasks"].append({"task": task, "done": False, "due_date": due_date})
        self.save_data()

    def mark_task_done(self, task_id):
        self.data["tasks"].pop(task_id)
        self.data["medals"] += 1
        self.save_data()

    def add_reward(self, reward, medal_cost):
        self.data["rewards"].append({"reward": reward, "medal_cost": medal_cost})
        self.save_data()

    def claim_reward(self, reward_id):
        reward = self.data["rewards"].pop(reward_id)
        if self.data["medals"] >= reward["medal_cost"]:
            self.data["medals"] -= reward["medal_cost"]
            self.save_data()
            return True
        else:
            self.data["rewards"].append(reward)  # Put reward back
            self.save_data()
            return False

    def get_tasks(self, due_date=None):
        if due_date:
            return [
                (index, task["task"], task["done"], task.get("due_date"))
                for index, task in enumerate(self.data["tasks"])
                if task.get("due_date") == due_date
            ]
        return [
            (index, task["task"], task["done"], task.get("due_date"))
            for index, task in enumerate(self.data["tasks"])
        ]

    def get_rewards(self):
        return self.data["rewards"]


def get_storage(page, username):
    """
    Factory function to initialize the appropriate storage backend.
    Uses LocalStorage for web platforms and SQLiteStorage for non-web platforms.
    """
    if page.web:  # Check if the app is running in a web browser
        print("Running in a web browser. Using LocalStorage for storage.")
        return LocalStorage(page, username)
    else:
        print("Running on a non-web platform. Using SQLiteStorage for storage.")
        return SQLiteStorage(username)
