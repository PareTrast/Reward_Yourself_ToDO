import os
import shutil
import flet as ft
import json
import asyncio  # For non-blocking delays


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

    async def load_data(self):
        retries = 5
        while retries > 0:
            try:
                data = self.page.client_storage.get(self.username)
                if data:
                    self.data = json.loads(data)
                else:
                    self.data = {"tasks": [], "rewards": [], "medals": 0}
                self.medals = self.data["medals"]
                return
            except TimeoutError:
                retries -= 1
                await asyncio.sleep(1)  # Use asyncio.sleep for non-blocking delay
        raise TimeoutError(
            "Failed to initialize client_storage after multiple retries."
        )

    def save_data(self):
        self.page.client_storage.set(self.username, json.dumps(self.data))


class IndexedDBStorage(Storage):
    def __init__(self, db_name, store_name, js):
        self.js = js  # Store a reference to the js module
        self.db_name = db_name
        self.store_name = store_name
        self.data = {"tasks": [], "rewards": [], "medals": 0}
        self.init_db()

    def init_db(self):
        """
        Initialize the IndexedDB database and object store.
        """
        request = self.js.window.indexedDB.open(self.db_name, 1)
        request.onupgradeneeded = lambda event: self._create_store(event)

    def _create_store(self, event):
        db = event.target.result
        if not db.objectStoreNames.contains(self.store_name):
            db.createObjectStore(
                self.store_name, {"keyPath": "id", "autoIncrement": True}
            )

    def load_data(self):
        """
        Load data from IndexedDB.
        """
        db_request = self.js.window.indexedDB.open(self.db_name)
        db_request.onsuccess = lambda event: self._load_from_store(event)

    def _load_from_store(self, event):
        db = event.target.result
        transaction = db.transaction(self.store_name, "readonly")
        store = transaction.objectStore(self.store_name)
        get_request = store.get(1)  # Assuming a single record with ID 1
        get_request.onsuccess = lambda event: self._set_data(event)

    def _set_data(self, event):
        result = event.target.result
        if result:
            self.data = json.loads(result)

    def save_data(self):
        """
        Save data to IndexedDB.
        """
        db_request = self.js.window.indexedDB.open(self.db_name)
        db_request.onsuccess = lambda event: self._save_to_store(event)

    def _save_to_store(self, event):
        db = event.target.result
        transaction = db.transaction(self.store_name, "readwrite")
        store = transaction.objectStore(self.store_name)
        store.put(self.data)


def get_storage(page, username):
    """
    Factory function to initialize the appropriate storage backend.
    Uses IndexedDB for web platforms and SQLiteStorage for non-web platforms.
    """
    if page.web:  # Check if the app is running in a web browser
        print("Running in a web browser. Using IndexedDB for storage.")
        try:
            import js  # Import js only when running in a browser

            return IndexedDBStorage(
                db_name="RewardYourselfDB", store_name="UserData", js=js
            )
        except ModuleNotFoundError:
            raise RuntimeError(
                "The 'js' module is only available in a browser environment."
            )
    else:
        print("Running on a non-web platform. Using SQLiteStorage for storage.")
        return SQLiteStorage(username)
