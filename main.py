import asyncio
import flet as ft
import os
from calendar_view import build_calendar
from database import Database
from todo_view import ToDoList
from user_manager import UserManager
from reward_view import reward_view
from history_view import history_view
import arrow
import time


async def main(page: ft.Page):

    page.title = "Reward Yourself"
    page.horizontal_alignment = page.vertical_alignment = "center"
    file_picker = ft.FilePicker()
    user_manager = UserManager(page)
    todo_list = None
    username = None
    selected_due_date = None
    is_web_environment = page.web

    def handle_change(e):
        nonlocal selected_due_date
        selected_due_date = e.control.value
        page.add(ft.Text(f"Date changed: {e.control.value.strftime('%Y-%m-%d')}"))

    def handle_dismissal(e):
        page.add(ft.Text(f"DatePicker dismissed."))

    async def _get_tokens(username=None):
        """Retrieves tokens based on the environment."""
        if page.web:
            access_token = page.client_storage.get("access_token")
            refresh_token = page.client_storage.get("refresh_token")

            return access_token, refresh_token
        else:
            user_storage = user_manager.get_user_storage()
            users_dir = "users"
            if os.path.exists(users_dir):
                for filename in os.listdir(users_dir):
                    if filename.endswith(".tokens"):
                        username = filename[:-7]  # Remove ".tokens"
                        tokens = user_storage.get_tokens(username)
                        if tokens:
                            access_token = tokens["access_token"]
                            refresh_token = tokens["refresh_token"]

                            return access_token, refresh_token
        return None, None

    async def check_login():
        username = None
        access_token, refresh_token = await _get_tokens()

        if not access_token or not refresh_token:
            return False, False, False, False

        if not isinstance(access_token, str):
            return False, False, False, False
        if not isinstance(refresh_token, str):
            return False, False, False, False

        supabase = await user_manager.get_supabase_client()
        try:
            user = await supabase.auth.get_user(access_token)
        except Exception as e:
            try:
                response = await supabase.auth.refresh_session(refresh_token)
                if response.session:
                    access_token = response.session.access_token
                    refresh_token = response.session.refresh_token

                    user = await supabase.auth.get_user(access_token)
                    if page.web:
                        page.client_storage.set("access_token", access_token)
                        page.client_storage.set("refresh_token", refresh_token)
                    else:
                        user_storage = user_manager.get_user_storage()
                        user_storage.store_tokens(username, access_token, refresh_token)
                else:
                    return False, False, False, False
            except Exception as e:
                return False, False, False, False

        if user:
            return (
                user.user.user_metadata["username"],
                user.user.id,
                access_token,
                refresh_token,
            )
        return False, False, False, False

    def show_login_view():
        page.views.clear()
        username_input = ft.TextField(label="Username")
        password_input = ft.TextField(
            label="Password", password=True, can_reveal_password=True
        )
        error_text = ft.Text("", color=ft.Colors.RED)

        async def login(e):
            nonlocal username, todo_list, access_token, refresh_token
            username = username_input.value
            password = password_input.value
            access_token, user_id, refresh_token = await user_manager.verify_user(
                username, password
            )
            if access_token and refresh_token:
                todo_list = ToDoList(
                    username=username, is_web_environment=is_web_environment
                )
                await todo_list.create_db_client()
                await todo_list.db.set_access_token(access_token, refresh_token)
                todo_list.set_user_id(user_id)
                todo_list.set_refresh_token(refresh_token)
                todo_list.set_access_token(access_token)
                page.views.clear()
                page.go("/")
            else:
                error_text.value = "Invalid username or password."
                page.update()

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
                            ft.TextButton(
                                "Register", on_click=lambda _: page.go("/register")
                            ),
                            error_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            )
        )
        page.update()

    def show_register_view(route):
        page.views.clear()

        async def register(e):
            access_token, user_id, refresh_token = await user_manager.register_user(
                register_username.value, register_password.value
            )

            if (
                access_token
                and refresh_token
                and isinstance(access_token, str)
                and isinstance(refresh_token, str)
            ):
                nonlocal username, todo_list
                username = register_username.value
                todo_list = ToDoList(
                    username=username, is_web_environment=is_web_environment
                )
                await todo_list.create_db_client()
                await todo_list.db.set_access_token(access_token, refresh_token)
                todo_list.set_user_id(user_id)
                todo_list.set_refresh_token(refresh_token)
                todo_list.set_access_token(access_token)
                user_storage = user_manager.get_user_storage()
                if page.web:
                    page.client_storage.set("access_token", access_token)
                    page.client_storage.set("refresh_token", refresh_token)
                else:
                    user_storage.store_tokens(username, access_token, refresh_token)
                page.views.clear()
                page.go("/")
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Username already taken."))
                page.snack_bar.open = True
                page.update()
            time.sleep(3)

        register_username = ft.TextField(label="Username")
        register_password = ft.TextField(
            label="Password", password=True, can_reveal_password=True
        )

        def back_to_login(e):
            page.go("/login")

        page.views.append(
            ft.View(
                "/register",
                [
                    register_username,
                    register_password,
                    ft.ElevatedButton("Register", on_click=register),
                    ft.TextButton("Back to Login", on_click=back_to_login),
                ],
            )
        )
        page.update()

    async def show_main_view():
        page.views.clear()
        nonlocal selected_due_date

        calendar_container = ft.Container(content=build_calendar(page), padding=10)
        task_input = ft.TextField(label="New Task", expand=True)
        reward_input = ft.TextField(label="New Reward", expand=True)
        medal_cost_input = ft.TextField(
            label="Medal Cost", keyboard_type=ft.KeyboardType.NUMBER, expand=True
        )
        medal_count = ft.Text(f"You have {0} medals.")

        task_list = ft.Column()
        reward_list = ft.Column()

        async def update_task_list():
            task_list.controls.clear()
            if todo_list:
                tasks = await todo_list.get_all_tasks()
                for task in tasks:
                    task_id = task["id"]
                    task_name = task["task"]
                    done = task["done"]
                    due_date = task.get("due_date", "None")
                    task_list.controls.append(
                        ft.Checkbox(
                            label=f"{task_name} (Due: {due_date})",
                            value=done,
                            on_change=lambda e, task_id=task_id, task_name=task_name: page.run_task(
                                mark_done, task_id, task_name
                            ),
                        )
                    )

                page.update()

        async def update_reward_list():
            reward_list.controls.clear()
            if todo_list:
                rewards = await todo_list.get_all_rewards()
                for reward in rewards:
                    reward_id = reward["id"]
                    reward_name = reward["reward"]
                    cost = reward["medal_cost"]
                    reward_list.controls.append(
                        ft.Checkbox(
                            label=f"{reward_name} - {cost} medals",
                            value=False,
                            on_change=lambda e, reward_id=reward_id, reward_name=reward_name: claim_reward(
                                reward_id, reward_name
                            ),
                        )
                    )
                page.update()

        async def mark_done(task_id, task_name):
            if todo_list:
                await todo_list.mark_task_done(task_id, task_name)
                await update_task_list()

        async def add_task(e):
            nonlocal selected_due_date
            if todo_list:
                if task_input.value:
                    due_date_str = (
                        selected_due_date.strftime("%Y-%m-%d")
                        if selected_due_date
                        else None
                    )
                    await todo_list.add_new_task(
                        {
                            "username": username,
                            "task": task_input.value,
                            "done": False,
                            "due_date": due_date_str,
                        }
                    )
                    task_input.value = ""
                    selected_due_date = None
                    await update_task_list()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Please enter a task."))
                    page.snack_bar.open = True
                    page.update()

        async def add_reward(e):
            if todo_list:
                if reward_input.value and medal_cost_input.value.isdigit():
                    await todo_list.add_new_reward(
                        {
                            "username": username,
                            "reward": reward_input.value,
                            "medal_cost": int(medal_cost_input.value),
                        }
                    )
                    reward_input.value = ""
                    medal_cost_input.value = ""
                    await update_reward_list()
                else:
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Please enter valid reward details.")
                    )
                    page.snack_bar.open = True
                    page.update()

        async def claim_reward(reward_id, reward_name):
            if todo_list:
                await todo_list.claim_reward(reward_id, reward_name)
                await update_reward_list()

        page.views.append(
            ft.View(
                "/",
                [
                    ft.SafeArea(
                        ft.Container(
                            content=ft.ListView(
                                controls=[
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "Reward Yourself",
                                                size=30,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    calendar_container,
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    task_input,
                                                    ft.ElevatedButton(
                                                        "Pick Date",
                                                        on_click=lambda e: page.open(
                                                            ft.DatePicker(
                                                                first_date=arrow.now(),
                                                                on_change=handle_change,
                                                                on_dismiss=handle_dismissal,
                                                            )
                                                        ),
                                                    ),
                                                    ft.ElevatedButton(
                                                        "Add Task", on_click=add_task
                                                    ),
                                                ],
                                                expand=True,
                                            ),
                                            ft.Container(
                                                content=task_list, expand=True
                                            ),
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
                                    ),
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
                                ft.IconButton(
                                    icon=ft.Icons.HISTORY,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda _: page.go("/history"),
                                ),
                            ]
                        ),
                    ),
                ],
            )
        )

        await update_task_list()

    async def route_change(route):
        page.views.clear()
        nonlocal todo_list, username, access_token, refresh_token
        if not todo_list:
            username, user_id, access_token, refresh_token = await check_login()
            if username:

                todo_list = ToDoList(
                    username=username, is_web_environment=is_web_environment
                )
                todo_list.set_user_id(user_id)
                todo_list.set_refresh_token(refresh_token)
                todo_list.set_access_token(access_token)
                await todo_list.create_db_client()

                if (
                    access_token
                    and refresh_token
                    and isinstance(access_token, str)
                    and isinstance(refresh_token, str)
                ):
                    await todo_list.db.set_access_token(access_token, refresh_token)
        if todo_list:
            if page.route == "/rewards":
                page.views.append(reward_view(page, todo_list))
            elif page.route == "/history":
                page.views.append(history_view(page, todo_list))
            else:
                await show_main_view()
        elif page.route == "/login":
            show_login_view()
        elif page.route == "/register":
            show_register_view(route)
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
        page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.overlay.append(file_picker)

    username, user_id, access_token, refresh_token = await check_login()
    if username:

        todo_list = ToDoList(username=username, is_web_environment=is_web_environment)
        todo_list.set_user_id(user_id)
        todo_list.set_refresh_token(refresh_token)
        await todo_list.create_db_client()

        if (
            access_token
            and refresh_token
            and isinstance(access_token, str)
            and isinstance(refresh_token, str)
        ):
            await todo_list.db.set_access_token(access_token, refresh_token)
        await route_change(page.route)
    else:
        show_login_view()


ft.app(target=main)
