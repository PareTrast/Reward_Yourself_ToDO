# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\history_view.py
import flet as ft
from todo_view import ToDoList  # ToDoList is now synchronous
import arrow


# Make history_view synchronous
def history_view(page: ft.Page, todo_list: ToDoList):
    task_history_list = ft.ListView(
        expand=True, spacing=5
    )  # Use ListView for scrolling
    reward_history_list = ft.ListView(
        expand=True, spacing=5
    )  # Use ListView for scrolling

    # Make synchronous
    def update_history_lists():
        task_history_list.controls.clear()
        reward_history_list.controls.clear()

        if not todo_list:
            task_history_list.controls.append(ft.Text("Error: Not logged in."))
            reward_history_list.controls.append(ft.Text("Error: Not logged in."))
            page.update()
            return

        print("Updating history lists...")
        task_history = todo_list.get_task_history()  # Sync call
        reward_history = todo_list.get_reward_history()  # Sync call

        # Populate Task History
        if task_history:
            for task in task_history:
                try:
                    # Use try-except for robust date parsing
                    timestamp_str = arrow.get(task.get("timestamp", "")).format(
                        "YYYY-MM-DD HH:mm"
                    )
                except (arrow.parser.ParserError, TypeError):
                    timestamp_str = "Invalid Date"
                description = task.get("description", "No description")
                task_history_list.controls.append(
                    ft.Text(f"{timestamp_str} - Task: {description}")
                )
        else:
            task_history_list.controls.append(ft.Text("No task history yet."))

        # Populate Reward History
        if reward_history:
            for reward in reward_history:
                try:
                    timestamp_str = arrow.get(reward.get("timestamp", "")).format(
                        "YYYY-MM-DD HH:mm"
                    )
                except (arrow.parser.ParserError, TypeError):
                    timestamp_str = "Invalid Date"
                description = reward.get("description", "No description")
                reward_history_list.controls.append(
                    ft.Text(f"{timestamp_str} - Reward: {description}")
                )
        else:
            reward_history_list.controls.append(ft.Text("No reward history yet."))

        print("History lists updated.")
        page.update()

    # Initial population (call directly)
    update_history_lists()

    return ft.View(
        "/history",
        [
            ft.AppBar(
                title=ft.Text("History"),
                leading=ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    tooltip="Back to Tasks",
                    on_click=lambda _: page.go("/"),
                ),
            ),
            ft.Column(  # Use a Column to structure the sections
                [
                    ft.Text("Task History", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    task_history_list,  # Add the ListView here
                    ft.Divider(height=20),
                    ft.Text("Reward History", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    reward_history_list,  # Add the ListView here
                ],
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE,  # Allow the whole column to scroll if needed
            ),
            # Keep the same BottomAppBar as main view for consistent navigation
            ft.BottomAppBar(
                bgcolor=ft.colors.BLUE_GREY_700,
                shape=ft.NotchShape.CIRCULAR,
                content=ft.Row(
                    controls=[
                        ft.IconButton(  # ToDo View
                            icon=ft.icons.CHECK_BOX_ROUNDED,
                            tooltip="Tasks",
                            icon_color=ft.colors.WHITE,
                            on_click=lambda _: page.go("/"),
                        ),
                        ft.Container(expand=True),  # Spacer
                        ft.IconButton(  # Rewards View
                            icon=ft.icons.STAR_RATE_ROUNDED,
                            tooltip="Rewards",
                            icon_color=ft.colors.WHITE,
                            on_click=lambda _: page.go("/rewards"),
                        ),
                        ft.IconButton(  # History View (Current)
                            icon=ft.icons.HISTORY,
                            tooltip="History",
                            icon_color=ft.colors.WHITE,
                            selected=True,  # Indicate current view
                            on_click=lambda _: page.go("/history"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ),
        ],
        padding=10,
    )
