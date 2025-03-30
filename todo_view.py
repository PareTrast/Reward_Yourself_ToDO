import sqlite3
import os
import shutil

class ToDoList:
    def __init__(self, username):
        db_filename = f"{username}_todo.db"
        self.db_path = os.path.join("users", db_filename)
        os.makedirs("users", exist_ok=True)
        self.create_tables()
        self.load_data()

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                done INTEGER,
                due_date TEXT NULL
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reward TEXT,
                medal_cost INTEGER
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS medals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count INTEGER
            )
        """
        )
        cursor.execute("INSERT OR IGNORE INTO medals (count) VALUES (0)")
        conn.commit()
        conn.close()

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM medals LIMIT 1")
        result = cursor.fetchone()
        self.medals = result[0] if result else 0
        conn.close()

    def add_task(self, task, due_date=None):
        due_date = due_date or None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task, done, due_date) VALUES (?, ?, ?)", (task, 0, due_date))
        conn.commit()
        conn.close()

    def mark_task_done(self, task_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE medals SET count = count + 1")
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        self.load_data()

    def add_reward(self, reward, medal_cost):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rewards (reward, medal_cost) VALUES (?, ?)",
            (reward, medal_cost),
        )
        conn.commit()
        conn.close()

    def claim_reward(self, reward_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reward, medal_cost FROM rewards WHERE id = ?", (reward_id,)
        )
        result = cursor.fetchone()
        if result:
            reward, medal_cost = result
            if self.medals >= medal_cost:
                cursor.execute("UPDATE medals SET count = count - ?", (medal_cost,))
                cursor.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
                conn.commit()
                conn.close()
                self.load_data()
                return True
            else:
                return False
        else:
            conn.close()
            return None

    def get_tasks(self, due_date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if due_date:
            cursor.execute("SELECT id, task, done, due_date FROM tasks WHERE due_date = ?", (due_date,))
        else:
            cursor.execute("SELECT id, task, done, due_date FROM tasks")
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_date_range(self, start_date, end_date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task, done, due_date FROM tasks WHERE due_date BETWEEN ? AND ?",
            (start_date, end_date),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_rewards(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, reward, medal_cost FROM rewards")
        rewards = cursor.fetchall()
        conn.close()
        return rewards

    def export_data(self, export_path):
        shutil.copy(self.db_path, export_path)

    def import_data(self, import_path):
        shutil.copy(import_path, self.db_path)
        self.load_data()
