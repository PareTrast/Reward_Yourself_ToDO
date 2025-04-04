import flet as ft
from todo_view import ToDoList
import arrow


def history_view(page: ft.Page, todo_list: ToDoList):
    task_history_list = ft.Column()
    reward_history_list = ft.Column()

    async def update_history_lists():  # Make this an async function
        task_history_list.controls.clear()
        reward_history_list.controls.clear()

        task_history = await todo_list.get_task_history()  # Await the coroutine
        reward_history = await todo_list.get_reward_history()  # Await the coroutine

        for task in task_history:
            timestamp = arrow.get(task["timestamp"]).format("YYYY-MM-DD HH:mm:ss")
            task_history_list.controls.append(
                ft.Text(f"Task: {task['description']} - Completed at: {timestamp}")
            )

        for reward in reward_history:
            timestamp = arrow.get(reward["timestamp"]).format("YYYY-MM-DD HH:mm:ss")
            reward_history_list.controls.append(
                ft.Text(f"Reward: {reward['description']} - Claimed at: {timestamp}")
            )

        page.update()

    page.run_task(update_history_lists)  # await the call to update_history_lists

    return ft.View(
        "/history",
        [
            ft.AppBar(
                title=ft.Text("History"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")
                ),
            ),
            ft.Text("Task History", weight=ft.FontWeight.BOLD),
            task_history_list,
            ft.Text("Reward History", weight=ft.FontWeight.BOLD),
            reward_history_list,
        ],
    )
