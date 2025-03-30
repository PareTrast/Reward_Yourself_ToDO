import flet as ft
import os
from calendar_view import build_calendar
from todo_view import ToDoList
from user_manager import UserManager
import arrow


def main(page: ft.Page):
    print("main function started")
    page.title = "Reward Yourself"
    page.horizontal_alignment = page.vertical_alignment = "center"
    file_picker = ft.FilePicker()
    user_manager = UserManager()
    todo_list = None
    username = None
    selected_due_date = None
    

    def handle_change(e):
        nonlocal  selected_due_date
        selected_due_date = e.control.value
        page.add(ft.Text(f"Date changed: {e.control.value.strftime('%Y-%m-%d')}"))
        

    def handle_dismissal(e):
        page.add(ft.Text(f"DatePicker dismissed."))

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

    def show_register_view(route):
        def register(e):
            if user_manager.register_user(
                register_username.value, register_password.value
            ):
                # page.views.clear()
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
        def back_to_login(e):
            #page.views.pop()
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
        page.go("/register")

    def logout():
        nonlocal todo_list, username
        todo_list = None
        username = None
        page.go("/login")

    def show_main_view():
        
        calendar_container = ft.Container(
            content = build_calendar(page), # add the calendar
            padding=10
        )
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
                for task_id, task, done, selected_date in tasks:
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
            nonlocal selected_due_date
            if task_input.value:
                due_date_str = selected_due_date.strftime("%Y-%m-%d") if selected_due_date else None
                todo_list.add_task(task_input.value, due_date_str)
                task_input.value = ""
                selected_due_date = None
                update_task_list()
                page.update()
            else:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Please enter a task.")
                )
                page.snack_bar.open = True
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
                                    ft.Row(
                                        [
                                            ft.Text("Reward Yourself", size=30, weight=ft.FontWeight.BOLD),
                                            ft.IconButton(
                                                icon=ft.Icons.LOGOUT,
                                                on_click=lambda _: logout(),
                                                tooltip="Logout"
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
                                                            first_date = arrow.now(),
                                                            on_change=handle_change,
                                                            on_dismiss=handle_dismissal,        
                                                            )
                                                        )
                                                    ),
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
            show_register_view(route)
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
ft.app(target=main, export_asgi_app=True)