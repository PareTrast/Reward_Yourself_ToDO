# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\main.py
import flet as ft
import os
import sys
import json
from calendar_view import build_calendar
from todo_view import ToDoList, MEDALS_PER_TASK
from user_manager import UserManager  # Keep UserManager import for its own use
from reward_view import reward_view
from history_view import history_view
import arrow
import time
import config_loader


# --- Session file handling (unchanged) ---
def read_tokens_from_session():
    """Reads the access_token and refresh_token from session.json."""
    try:
        with open("session.json", "r") as file:
            content = file.read()
            if not content:
                return None, None
            session_data = json.loads(content)
            access_token = session_data.get("access_token")
            refresh_token = session_data.get("refresh_token")
            if isinstance(access_token, str) and isinstance(refresh_token, str):
                return access_token, refresh_token
            else:
                print("Invalid token format found in session.json.")
                return None, None
    except FileNotFoundError:
        return None, None
    except json.JSONDecodeError:
        print("Error decoding session.json.")
        return None, None
    except Exception as e:
        print(f"Error reading session.json: {e}")
        return None, None


def write_tokens_to_session(access_token, refresh_token):
    """Writes the access_token and refresh_token to session.json."""
    if not isinstance(access_token, str) or not isinstance(refresh_token, str):
        print("Error: Attempted to write non-string tokens to session.json.")
        return
    try:
        with open("session.json", "w") as file:
            json.dump(
                {"access_token": access_token, "refresh_token": refresh_token}, file
            )
        print("Tokens written to session.json.")
    except Exception as e:
        print(f"Error writing to session.json: {e}")


# --- Main Application Function ---
def main(page: ft.Page):
    if config_loader.CONFIG_ERROR:
        page.add(
            ft.Column(
                [
                    ft.Text(
                        "Application Configuration Error", size=20, color=ft.colors.RED
                    ),
                    ft.Text(config_loader.CONFIG_ERROR),
                    ft.Text("Please check config.json and build includes."),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()
        return

    page.title = "Reward Yourself"
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.SYSTEM

    # --- State Variables ---
    user_manager = UserManager(page)  # Initialize UserManager
    todo_list: ToDoList = None
    username: str = None
    selected_due_date = None
    is_web_environment = page.web
    # --- Central UI element for medal display ---
    current_medal_count_display_main = ft.Text(
        "Medals: -", tooltip="Your current medal balance"
    )
    # --- End modification ---

    # --- UI Elements (Shared/Persistent) ---
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # --- Token Management (unchanged) ---
    def _get_tokens():
        if page.web:
            try:
                access_token = page.client_storage.get("access_token")
                refresh_token = page.client_storage.get("refresh_token")
                if not access_token or not refresh_token:
                    return None, None
                if isinstance(access_token, str) and isinstance(refresh_token, str):
                    return access_token, refresh_token
                else:
                    page.client_storage.remove("access_token")
                    page.client_storage.remove("refresh_token")
                    return None, None
            except Exception as e:
                print(f"Error retrieving tokens from client storage: {e}")
                return None, None
        else:
            return read_tokens_from_session()

    def _clear_tokens():
        print("Clearing stored tokens...")
        if page.web:
            page.client_storage.remove("access_token")
            page.client_storage.remove("refresh_token")
        else:
            try:
                if os.path.exists("session.json"):
                    os.remove("session.json")
                    print("Removed session.json.")
            except OSError as e:
                print(f"Error removing session.json: {e}")

    def _store_tokens(acc_token, ref_token):
        print("Storing tokens...")
        if page.web:
            page.client_storage.set("access_token", acc_token)
            page.client_storage.set("refresh_token", ref_token)
        else:
            write_tokens_to_session(acc_token, ref_token)

    # --- Central Medal Count Update Function ---
    def update_main_medal_display(new_count: int | None = None):
        """Fetches medal count if needed and updates the main view's UI text.
        Does NOT call page.update()."""
        display_value = "Medals: Error"
        count_to_display = None

        if new_count is not None:
            print(f"Updating main medal display with provided count: {new_count}")
            count_to_display = new_count
        elif todo_list:  # Fetch only if not provided and logged in
            print("Fetching medal count for main display update...")
            fetched_count = todo_list.get_medal_count()  # Synchronous call
            if fetched_count is not None:
                count_to_display = fetched_count
            else:
                print("Failed to fetch medal count.")  # Keep error message

        if count_to_display is not None:
            display_value = f"Medals: {count_to_display}"
        elif not todo_list:  # Handle case where user is logged out
            display_value = "Medals: N/A"
        # else: display_value remains "Medals: Error" if fetch failed

        current_medal_count_display_main.value = display_value
        # Let the caller decide when to call page.update()
        print(f"Main medal display updated to: {display_value}")

    # --- End modification ---

    # --- Authentication Logic ---
    def check_login():
        """Checks login status, initializes ToDoList, returns True if logged in."""
        nonlocal username, todo_list
        access_token, refresh_token = _get_tokens()
        if not access_token or not refresh_token:
            return False

        supabase_client = user_manager.get_supabase_client()
        if not supabase_client:
            _clear_tokens()
            return False

        try:
            print("check_login: Verifying token...")
            try:
                # Set session for subsequent client calls (like get_user)
                supabase_client.auth.set_session(access_token, refresh_token)
            except Exception as e:
                print(f"Error setting session: {e}")
                _clear_tokens()
                return False

            user_response = supabase_client.auth.get_user()
            user = user_response.user
            if user:
                print(f"check_login: Token valid for user ID: {user.id}")
                # Try getting username from metadata first (set during signup or profile update)
                stored_username = user.user_metadata.get("username")
                if stored_username:
                    username = stored_username
                elif user.email and "@placeholder.com" in user.email:
                    # Fallback to extracting from email if metadata username is missing
                    username = user.email.split("@")[0]
                else:
                    # Further fallback if email format is unexpected
                    print(
                        "Warning: Could not determine username from metadata or email."
                    )
                    username = f"User_{user.id[:5]}"

                if not todo_list:
                    # --- Remove user_manager argument ---
                    todo_list = ToDoList(username, is_web_environment, supabase_client)
                elif (
                    not todo_list.supabase_client
                ):  # Ensure client is set if todo_list existed
                    todo_list.supabase_client = supabase_client
                # --- Remove user_manager assignment ---
                # if not hasattr(todo_list, 'user_manager') or not todo_list.user_manager:
                #     todo_list.user_manager = user_manager
                # --- End modification ---
                todo_list.user_id = user.id  # Set user_id here
                todo_list.set_access_token(
                    access_token, refresh_token
                )  # Ensure ToDoList has tokens
                _store_tokens(
                    access_token, refresh_token
                )  # Store potentially refreshed tokens
                # --- Trigger initial medal update after successful login/validation ---
                update_main_medal_display()
                # --- End modification ---
                return True  # Successfully logged in
            else:
                # This case might indicate an issue with get_user despite set_session working
                print("check_login: set_session succeeded but get_user failed.")
                _clear_tokens()
                return False

        except Exception as e:
            print(f"check_login: Token invalid/expired ({e}). Attempting refresh...")
            try:
                print("check_login: Attempting explicit refresh...")
                refresh_response = supabase_client.auth.refresh_session()
                if not refresh_response or not refresh_response.session:
                    print("check_login: Explicit refresh failed.")
                    _clear_tokens()
                    return False

                print("check_login: Explicit refresh successful, getting user again...")
                user_response_after_refresh = supabase_client.auth.get_user()
                user = user_response_after_refresh.user

                if user:
                    print("check_login: Refresh successful and token still valid.")
                    current_session = supabase_client.auth.get_session()
                    if not current_session:
                        print(
                            "Error: User found but session is missing after successful refresh."
                        )
                        _clear_tokens()
                        return False

                    new_access_token = current_session.access_token
                    new_refresh_token = current_session.refresh_token

                    # Try getting username from metadata first
                    stored_username = user.user_metadata.get("username")
                    if stored_username:
                        username = stored_username
                    elif user.email and "@placeholder.com" in user.email:
                        username = user.email.split("@")[0]
                    else:
                        print(
                            "Warning: Could not determine username from metadata or email after refresh."
                        )
                        username = f"User_{user.id[:5]}"

                    if not todo_list:
                        # --- Remove user_manager argument ---
                        todo_list = ToDoList(
                            username, is_web_environment, supabase_client
                        )
                    elif not todo_list.supabase_client:
                        todo_list.supabase_client = supabase_client
                    # --- Remove user_manager assignment ---
                    # if not hasattr(todo_list, 'user_manager') or not todo_list.user_manager:
                    #     todo_list.user_manager = user_manager
                    # --- End modification ---
                    todo_list.user_id = user.id  # Set user_id here
                    todo_list.set_access_token(new_access_token, new_refresh_token)
                    _store_tokens(new_access_token, new_refresh_token)
                    # --- Trigger initial medal update after successful refresh ---
                    update_main_medal_display()
                    # --- End modification ---
                    return True  # Successfully refreshed and logged in
                else:
                    print("check_login: Refresh succeeded but get_user still failed.")
                    _clear_tokens()
                    return False
            except Exception as refresh_e:
                print(f"check_login: Error during refresh attempt: {refresh_e}")
                _clear_tokens()
                return False

    def perform_login(login_username, password, error_text_control):
        """Handles the login process."""
        nonlocal username, todo_list
        error_text_control.value = ""  # Clear previous errors
        page.update()

        if not login_username or not password:
            error_text_control.value = "Please enter username and password."
            page.update()
            return

        access_token, user_id, refresh_token = user_manager.verify_user(
            login_username, password
        )
        if access_token and user_id and refresh_token:
            username = login_username  # Use the provided login username
            supabase_client = user_manager.get_supabase_client()
            if not supabase_client:
                error_text_control.value = "Error initializing application services."
                page.update()
                return

            # Initialize ToDoList
            # --- Remove user_manager argument ---
            todo_list = ToDoList(username, is_web_environment, supabase_client)
            # --- End modification ---
            todo_list.set_access_token(access_token, refresh_token)
            todo_list.user_id = user_id  # Set user_id here
            _store_tokens(access_token, refresh_token)

            # Set session in the client *after* successful login
            try:
                supabase_client.auth.set_session(access_token, refresh_token)
                print("Session set in client after login.")
            except Exception as e:
                print(f"Error setting session after login: {e}")

            page.go("/")
        else:
            error_text_control.value = "Login failed. Check username/password."
            _clear_tokens()
            page.update()

    def perform_registration(reg_username, password, error_text_control):
        """Handles the registration process."""
        nonlocal username, todo_list
        error_text_control.value = ""  # Clear previous errors
        page.update()

        if not reg_username or not password:
            error_text_control.value = "Please enter username and password."
            page.update()
            return
        if len(password) < 6:
            error_text_control.value = "Password must be at least 6 characters."
            page.update()
            return

        access_token, user_id, refresh_token = user_manager.register_user(
            reg_username, password
        )
        if access_token and user_id and refresh_token:
            username = reg_username  # Use the provided registration username
            supabase_client = user_manager.get_supabase_client()
            if not supabase_client:
                error_text_control.value = (
                    "Error initializing application services after registration."
                )
                page.update()
                return

            # Initialize ToDoList
            # --- Remove user_manager argument ---
            todo_list = ToDoList(username, is_web_environment, supabase_client)
            # --- End modification ---
            todo_list.set_access_token(access_token, refresh_token)
            todo_list.user_id = user_id  # Set user_id here
            _store_tokens(access_token, refresh_token)

            # Set session in the client *after* successful registration
            try:
                supabase_client.auth.set_session(access_token, refresh_token)
                print("Session set in client after registration.")
            except Exception as e:
                print(f"Error setting session after registration: {e}")

            page.go("/")
        else:
            error_text_control.value = (
                "Registration failed. User might already exist or invalid input."
            )
            _clear_tokens()
            page.update()

    def perform_logout():
        """Logs the user out and clears session."""
        nonlocal username, todo_list
        print("Performing logout...")
        supabase_client = user_manager.get_supabase_client()
        if supabase_client:
            try:
                supabase_client.auth.sign_out()
                print("Signed out from Supabase.")
            except Exception as e:
                print(f"Error during Supabase sign out: {e}")

        _clear_tokens()
        username = None
        todo_list = None
        current_medal_count_display_main.value = "Medals: N/A"
        page.go("/login")

    # --- View Definitions ---
    def show_login_view():
        username_input = ft.TextField(
            label="Username", autofocus=True, on_submit=lambda e: password_input.focus()
        )
        password_input = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            on_submit=lambda e: perform_login(
                username_input.value.strip(),
                password_input.value,
                error_text,
            ),
        )
        error_text = ft.Text("", color=ft.colors.RED)
        return ft.View(
            "/login",
            [
                ft.AppBar(title=ft.Text("Login"), automatically_imply_leading=False),
                ft.Column(
                    [
                        username_input,
                        password_input,
                        ft.ElevatedButton(
                            "Login",
                            on_click=lambda e: perform_login(
                                username_input.value.strip(),
                                password_input.value,
                                error_text,
                            ),
                        ),
                        ft.TextButton(
                            "Register", on_click=lambda _: page.go("/register")
                        ),
                        error_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    width=300,
                ),
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def show_register_view():
        register_username = ft.TextField(
            label="Username",
            autofocus=True,
            on_submit=lambda e: register_password.focus(),
        )
        register_password = ft.TextField(
            label="Password (min 6 chars)",
            password=True,
            can_reveal_password=True,
            on_submit=lambda e: perform_registration(
                register_username.value.strip(),
                register_password.value,
                error_text,
            ),
        )
        error_text = ft.Text("", color=ft.colors.RED)
        return ft.View(
            "/register",
            [
                ft.AppBar(title=ft.Text("Register")),
                ft.Column(
                    [
                        register_username,
                        register_password,
                        ft.ElevatedButton(
                            "Register",
                            on_click=lambda e: perform_registration(
                                register_username.value.strip(),
                                register_password.value,
                                error_text,
                            ),
                        ),
                        error_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    width=300,
                ),
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def show_main_view():
        """Builds and displays the main ToDo view."""
        nonlocal selected_due_date

        calendar_container = ft.Container(content=build_calendar(page), padding=10)
        task_input = ft.TextField(
            label="New Task", expand=True, on_submit=lambda e: add_task(e)
        )
        task_list_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        selected_date_text = ft.Text("Due Date: None")

        def handle_date_change_main(e):
            nonlocal selected_due_date
            selected_due_date = e.control.value
            selected_date_text.value = (
                f"Due: {selected_due_date.strftime('%Y-%m-%d')}"
                if selected_due_date
                else "Due Date: None"
            )
            page.update()

        def handle_date_dismissal_main(e):
            print("DatePicker dismissed.")

        def update_task_list():
            task_list_view.controls.clear()
            if not todo_list:
                task_list_view.controls.append(ft.Text("Error: Not logged in."))
                return
            tasks = todo_list.get_all_tasks()
            if tasks:
                for task in tasks:
                    task_id, task_name, due_date_str = (
                        task.get("id"),
                        task.get("task", "Unnamed"),
                        task.get("due_date"),
                    )
                    if task_id is None:
                        continue
                    due_date_display = f" (Due: {due_date_str})" if due_date_str else ""
                    task_list_view.controls.append(
                        ft.Row(
                            [
                                ft.Text(
                                    f"{task_name}{due_date_display}",
                                    expand=True,
                                    tooltip=task_name,
                                ),
                                ft.IconButton(
                                    ft.icons.CHECK_CIRCLE_OUTLINE,
                                    tooltip="Mark as Done",
                                    on_click=lambda _, tid=task_id, tname=task_name: mark_done(
                                        tid, tname
                                    ),
                                    icon_color=ft.colors.GREEN_ACCENT_700,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        )
                    )
            else:
                task_list_view.controls.append(ft.Text("No tasks yet!"))

        def mark_done(task_id, task_name):
            print(f"Marking task done: ID={task_id}, Name={task_name}")
            if todo_list:
                success, returned_new_count = todo_list.mark_task_done(
                    task_id, task_name
                )
                if success:
                    page.snack_bar = ft.SnackBar(
                        ft.Text(
                            f"Task '{task_name}' completed! (+{MEDALS_PER_TASK} Medals)"
                        )
                    )
                    page.snack_bar.open = True
                    update_task_list()
                    update_main_medal_display(new_count=returned_new_count)
                else:
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Error completing task or updating medals.")
                    )
                    page.snack_bar.open = True
                page.update()
            else:
                print("Error: todo_list not available in mark_done.")

        def add_task(e):
            nonlocal selected_due_date
            if todo_list:
                task_text = task_input.value.strip()
                if task_text:
                    due_date_str = (
                        selected_due_date.strftime("%Y-%m-%d")
                        if selected_due_date
                        else None
                    )
                    new_task_data = {
                        "task": task_text,
                        "done": False,
                        "due_date": due_date_str,
                    }
                    added_task = todo_list.add_new_task(new_task_data)
                    if added_task:
                        task_input.value = ""
                        selected_due_date = None
                        selected_date_text.value = "Due Date: None"
                        task_input.focus()
                        update_task_list()
                        page.snack_bar = ft.SnackBar(ft.Text("Task added!"))
                        page.snack_bar.open = True
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text("Error adding task."))
                        page.snack_bar.open = True
                    page.update()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Please enter a task."))
                    page.snack_bar.open = True
                    task_input.focus()
                    page.update()
            else:
                print("Error: todo_list not available in add_task.")

        update_task_list()

        return ft.View(
            "/",
            [
                ft.AppBar(
                    title=ft.Text("Reward Yourself - ToDo"),
                    actions=[
                        current_medal_count_display_main,
                        ft.IconButton(
                            ft.icons.REFRESH,
                            tooltip="Refresh Medals",
                            on_click=lambda _: (
                                update_main_medal_display(),
                                page.update(),
                            ),
                        ),
                        ft.IconButton(
                            ft.icons.LOGOUT,
                            tooltip="Logout",
                            on_click=lambda _: perform_logout(),
                        ),
                    ],
                ),
                ft.Column(
                    [
                        calendar_container,
                        ft.Row(
                            [
                                task_input,
                                ft.IconButton(
                                    ft.icons.CALENDAR_MONTH,
                                    tooltip="Pick Due Date",
                                    on_click=lambda e: page.open(
                                        ft.DatePicker(
                                            first_date=arrow.now().datetime,
                                            last_date=arrow.now()
                                            .shift(years=+5)
                                            .datetime,
                                            help_text="Select task due date",
                                            on_change=handle_date_change_main,
                                            on_dismiss=handle_date_dismissal_main,
                                        )
                                    ),
                                ),
                                ft.IconButton(
                                    ft.icons.ADD_CIRCLE,
                                    tooltip="Add Task",
                                    on_click=add_task,
                                    icon_color=ft.colors.GREEN,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        selected_date_text,
                        ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                        ft.Text("Tasks", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        task_list_view,
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
            ],
            padding=10,
            bottom_appbar=build_bottom_app_bar("/"),
        )

    # --- Navigation ---
    def build_bottom_app_bar(current_route):
        return ft.BottomAppBar(
            bgcolor=ft.colors.BLUE_GREY_700,
            shape=ft.NotchShape.CIRCULAR,
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        ft.icons.CHECK_BOX_ROUNDED,
                        tooltip="Tasks",
                        icon_color=ft.colors.WHITE,
                        selected=(current_route == "/"),
                        on_click=lambda _: page.go("/"),
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.icons.STAR_RATE_ROUNDED,
                        tooltip="Rewards",
                        icon_color=ft.colors.WHITE,
                        selected=(current_route == "/rewards"),
                        on_click=lambda _: page.go("/rewards"),
                    ),
                    ft.IconButton(
                        ft.icons.HISTORY,
                        tooltip="History",
                        icon_color=ft.colors.WHITE,
                        selected=(current_route == "/history"),
                        on_click=lambda _: page.go("/history"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
        )

    # --- Modified route_change ---
    def route_change(route):
        print(f"Route change requested: {page.route}")
        current_route = page.route
        page.views.clear()

        is_logged_in = check_login()

        target_view = None

        if not is_logged_in:
            if current_route not in ["/login", "/register"]:
                print("Not logged in, redirecting to /login")
                page.route = "/login"
                target_view = show_login_view()
            elif current_route == "/login":
                target_view = show_login_view()
            else:
                target_view = show_register_view()
            current_medal_count_display_main.value = "Medals: N/A"
        else:
            if current_route in ["/login", "/register"]:
                print("Logged in, redirecting from auth page to /")
                page.route = "/"
                current_route = "/"

            if current_route == "/rewards":
                view = reward_view(page, todo_list, update_main_medal_display)
                view.bottom_appbar = build_bottom_app_bar(current_route)
                target_view = view
            elif current_route == "/history":
                view = history_view(page, todo_list)
                view.bottom_appbar = build_bottom_app_bar(current_route)
                target_view = view
            else:
                target_view = show_main_view()

            update_main_medal_display()  # Ensure medal count is updated on navigation

        if target_view:
            page.views.append(target_view)
        else:
            print("Error: No target view determined, falling back to login.")
            page.views.append(show_login_view())

        page.update()

    # --- End modification ---

    def view_pop(view):
        print(f"View popped: {view.route}")
        page.views.pop()
        top_view = page.views[-1] if page.views else None
        target_route = top_view.route if top_view else "/login"
        print(f"Navigating back to: {target_route}")
        page.go(target_route)

    # --- App Initialization ---
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    print("App initializing...")
    page.go(page.route)


# --- Run the App ---
if __name__ == "__main__":
    # os.environ["FLET_FORCE_WEB_SOCKETS"] = "true"
    ft.app(target=main)
