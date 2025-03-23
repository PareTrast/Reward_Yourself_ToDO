import flet as ft
from datetime import datetime
from database import ToDoList

def todo_view(page: ft.Page, todo_list: ToDoList):
    task_input = ft.TextField(label="New Task", expand=True)
    due_date_picker = ft.DatePicker(field_label_text="Due Date")
    task_list = ft.Column()

    def update_task_list():
        task_list.controls.clear()
        tasks = todo_list.get_tasks()
        tasks_by_date = {}
        for task_id, task, done, due_date in tasks:
            if due_date:
                if due_date not in tasks_by_date:
                    tasks_by_date[due_date] = []
                tasks_by_date[due_date].append((task_id, task, done, due_date))
            else:
                if "No Due Date" not in tasks_by_date:
                    tasks_by_date["No Due Date"] = []
                tasks_by_date["No Due Date"].append((task_id, task, done, due_date))

        for date, tasks in tasks_by_date.items():
            task_list.controls.append(ft.Text(f"Tasks for {date}"))
            for task_id, task, done, due_date in tasks:
                task_list.controls.append(
                    ft.Checkbox(
                        label=f"{task} (Due: {due_date if due_date else 'None'})",
                        value=done,
                        on_change=lambda e, task_id=task_id: mark_done(task_id),
                    )
                )
        page.update()

    def mark_done(task_id):
        todo_list.mark_task_done(task_id)
        update_task_list()
        page.update()

    def add_task(e):
        try:
            due_date = due_date_picker.value.strftime("%Y-%m-%d") if due_date_picker.value else None
            if task_input.value: #Added here
                todo_list.add_task(task_input.value, due_date)
            task_input.value = ""
            due_date_picker.value = None
            update_task_list()
            page.update()
        except Exception as ex:
            print(f"Error in add_task: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"An error occurred: {ex}"))
            page.snack_bar.open = True
            page.update()

    update_task_list()

    return ft.View(
        "/todo",
        [
            ft.AppBar(title=ft.Text("Todo List")),
            ft.Column(
                [
                    ft.Row([task_input, ft.Container(content=due_date_picker), ft.ElevatedButton("Add Task", on_click=add_task)]),
                    task_list,
                ],
                expand=True,
            ),
        ],
    )