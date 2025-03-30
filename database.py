import sqlite3
import os
import shutil
import flet as ft
import json



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
        self.medals = result[0] if result else 0

    def add_task(self, task, due_date=None):
        due_date = due_date or None
        self.cursor.execute("INSERT INTO tasks (task, done, due_date) VALUES (?, ?, ?)", (task, 0, due_date))
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
                self.cursor.execute("UPDATE medals SET count = count - ?", (medal_cost,))
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
            self.cursor.execute("SELECT id, task, done, due_date FROM tasks WHERE due_date = ?", (due_date,))
        else:
            self.cursor.execute("SELECT id, task, done, due_date FROM tasks")
        return self.cursor.fetchall()

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
        self.load_data()

    def load_data(self):
        data = self.page.client_storage.get(self.username)
        if data:
            self.data = json.loads(data)
        else:
            self.data = {"tasks": [], "rewards": [], "medals": 0}

    def save_data(self):
        self.page.client_storage.set(self.username, json.dumps(self.data))

    def create_tables(self):
        pass  # No tables in localStorage

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
            return [task for task in self.data["tasks"] if task["due_date"] == due_date]
        return self.data["tasks"]
    
    def get_tasks_by_date_range(self, start_date, end_date):
        return [task for task in self.data["tasks"] if start_date <= task["due_date"] <= end_date]

    def get_rewards(self):
        return self.data["rewards"]

    def export_data(self, export_path):
        with open(export_path, "w") as f:
            json.dump(self.data, f)

    def import_data(self, import_path):
        try:
            with open(import_path, "r") as f:
                self.data = json.load(f)
            self.save_data()
        except FileNotFoundError:
            pass

