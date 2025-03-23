import flet as ft
import sqlite3
import shutil
import hashlib
import os

class UserManager:
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    def register_user(self, username, password):
        user_path = os.path.join(self.users_dir, username)
        if os.path.exists(user_path):
            return False
        os.makedirs(user_path, exist_ok=True)
        
        salt = os.urandom(16)
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        with open(user_path, "wb") as f:
            f.write(salt + hashed_password.encode())
        return True

    def verify_user(self, username, password):
        user_path = os.path.join(self.users_dir, username)
        if not os.path.exists(user_path):
            return False
        with open(user_path, "rb") as f:
            salt = f.read(16)
            stored_hash = f.read().decode()
        hashed_password = hashlib.sha256(salt + password.encode()).hexdigest()
        return hashed_password == stored_hash

class ToDoList:
    def __init__(self, username):
        db_filename = f"{username}_todo_data.db"
        self.db_path = os.path.join("users", username, db_filename)
        print(f"ToDoList db_path: {self.db_path}")
        # os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
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
                done INTEGER
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

    def add_task(self, task):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task, done) VALUES (?, ?)", (task, 0))
        conn.commit()
        conn.close()

    def mark_task_done(self, task_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        cursor.execute("UPDATE medals SET count = count + 1")
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

    def get_tasks(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, done FROM tasks")
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

def main(page: ft.Page):
    print("main function started")
    page.title = "Reward Yourself"
    page.horizontal_alignment = page.vertical_alignment = "center"
    file_picker = ft.FilePicker()
    user_manager = UserManager()
    todo_list = None
    username = None

    def check_login():
        users_dir = "users"
        if os.path.exists(users_dir):
            if os.listdir(users_dir):
                username = os.listdir(users_dir)[0]
                if username:
                    return username
                else:
                    return False
            else:
                return False
        else:
            return False

    def show_login_view():
        username_input = ft.TextField(label="Username")
        password_input = ft.TextField(label="Password", password=True, can_reveal_password=True)
        error_text = ft.Text("", color=ft.Colors.RED)
        def login(e):
            nonlocal username, todo_list
            username = username_input.value
            password = password_input.value
            if user_manager.verify_user(username, password):
                todo_list = ToDoList(username)
                page.views.clear()
                page.go("/")
            else:
                error_text.value = "Invalid username or password."
                page.update()

        page.views.clear()
        page.views.append(
            ft.View(
                "/login",
                [
                    ft.AppBar(title=ft.Text("Login")),
                    ft.Column(
                        [
                            username_input,
                            password_input,
                            ft.ElevatedButton("Login", on_click=login),
                            ft.TextButton("Register", on_click=show_register_view),
                            error_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            )
        )
        page.go("/login")

    def show_register_view(e):
        def register(e):
            if user_manager.register_user(
                register_username.value, register_password.value
            ):
                page.views.clear()
                show_login_view()
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Username already taken."))
                page.snack_bar.open = True
                page.update()

        register_username = ft.TextField(label="Username")
        register_password = ft.TextField(
            label="Password", password=True, can_reveal_password=True
        )
        page.views.append(
            ft.View(
                "/register",
                [
                    register_username,
                    register_password,
                    ft.ElevatedButton("Register", on_click=register),
                    ft.TextButton("Back to Login", on_click=lambda e: page.views.pop()),
                ],
            )
        )
        page.go("/register")

    def show_main_view():
        task_input = ft.TextField(label="New Task", expand=True)
        reward_input = ft.TextField(label="New Reward", expand=True)
        medal_cost_input = ft.TextField(
            label="Medal Cost", keyboard_type=ft.KeyboardType.NUMBER, expand=True
        )
        medal_count = ft.Text(f"You have {todo_list.medals} medals.")

        task_list = ft.Column()
        reward_list = ft.Column()

        def update_task_list():
            task_list.controls.clear()
            if todo_list:
                tasks = todo_list.get_tasks()
                for task_id, task, done in tasks:
                    task_list.controls.append(
                        ft.Checkbox(
                            label=task,
                            value=done,
                            on_change=lambda e, task_id=task_id: mark_done(task_id),
                        )
                    )
            page.update()

        def update_reward_list():
            reward_list.controls.clear()
            if todo_list:
                rewards = todo_list.get_rewards()
                for reward_id, reward, cost in rewards:
                    reward_list.controls.append(
                        ft.Checkbox(
                            label=f"{reward} - {cost} medals",
                            value=False,
                            on_change=lambda e, reward_id=reward_id: claim_reward(
                                reward_id
                            ),
                        )
                    )
            page.update()

        def mark_done(task_id):
            todo_list.mark_task_done(task_id)
            update_task_list()
            medal_count.value = f"You have {todo_list.medals} medals."
            page.update()

        def add_task(e):
            todo_list.add_task(task_input.value)
            task_input.value = ""
            update_task_list()
            page.update()

        def add_reward(e):
            todo_list.add_reward(reward_input.value, int(medal_cost_input.value))
            reward_input.value = ""
            medal_cost_input.value = ""
            update_reward_list()
            page.update()

        def claim_reward(reward_id):
            result = todo_list.claim_reward(reward_id)
            if result is True:
                medal_count.value = f"You have {todo_list.medals} medals."
                update_reward_list()
                page.update()
            elif result is False:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Not enough medals to claim this reward.")
                )
                page.snack_bar.open = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Reward not found."))
                page.snack_bar.open = True
                page.update()

        update_task_list()
        update_reward_list()

        page.views.append(
            ft.View(
                "/",
                [
                    ft.SafeArea(
                        ft.Container(
                            content=ft.ListView(
                                controls=[
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    task_input,
                                                    ft.ElevatedButton(
                                                        "Add Task", on_click=add_task
                                                    ),
                                                ],
                                                expand=True,
                                            ),
                                            ft.Container(content=task_list, expand=True),
                                            ft.Row(
                                                [
                                                    ft.ElevatedButton(
                                                        "Export Data",
                                                        on_click=lambda _: file_picker.save_file(
                                                            allowed_extensions=["db"]
                                                        ),
                                                    ),
                                                    ft.ElevatedButton(
                                                        "Import Data",
                                                        on_click=lambda _: file_picker.pick_files(
                                                            allowed_extensions=["db"]
                                                        ),
                                                    ),
                                                ],
                                                expand=True,
                                            ),
                                        ],
                                        expand=True,
                                    )
                                ],
                                expand=True,
                            ),
                            padding=10,
                        )
                    ),
                    ft.BottomAppBar(
                        bgcolor=ft.Colors.BLACK38,
                        shape=ft.NotchShape.CIRCULAR,
                        content=ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.CHECK_BOX_ROUNDED,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda _: page.go("/"),
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.MONEY_ROUNDED,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda _: page.go("/rewards"),
                                ),
                            ]
                        ),
                    ),
                ],
            )
        )
        if page.route == "/rewards":
            page.views.append(
                ft.View(
                    "/rewards",
                    [
                        ft.SafeArea(
                            ft.Container(
                                content=ft.ListView(
                                    controls=[
                                        ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        reward_input,
                                                        medal_cost_input,
                                                        ft.ElevatedButton(
                                                            "Add Reward",
                                                            on_click=add_reward,
                                                        ),
                                                    ],
                                                    expand=True,
                                                ),
                                                ft.Container(
                                                    content=reward_list, expand=True
                                                ),
                                                medal_count,
                                            ],
                                            expand=True,
                                        )
                                    ],
                                    expand=True,
                                ),
                                padding=10,
                            )
                        ),
                        ft.BottomAppBar(
                            bgcolor=ft.Colors.BLACK38,
                            shape=ft.NotchShape.CIRCULAR,
                            content=ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.CHECK_BOX_ROUNDED,
                                        icon_color=ft.Colors.WHITE,
                                        on_click=lambda _: page.go("/"),
                                    ),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.MONEY_ROUNDED,
                                        icon_color=ft.Colors.WHITE,
                                        on_click=lambda _: page.go("/rewards"),
                                    ),
                                ]
                            ),
                        ),
                    ],
                )
            )
        page.update()

    def route_change(route):
        page.views.clear()
        if todo_list:
            show_main_view()
        elif page.route == "/login":
            show_login_view()
        elif page.route == "/register":
            show_register_view(e)
        page.go(page.route)

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.overlay.append(file_picker)

    username = check_login()
    if username:
        print(f"Main username: {username}") #added print statement
        todo_list = ToDoList(username)
        route_change(page.route)
    else:
        show_login_view()

ft.app(target=main, assets_dir="assets")