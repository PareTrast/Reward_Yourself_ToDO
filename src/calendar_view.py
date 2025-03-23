import flet as ft
from datetime import datetime, timedelta
from database import ToDoList  # Import your ToDoList class

def calendar_view(page: ft.Page, todo_list: ToDoList):
    def get_7_day_range():
        today = datetime.now().date()
        return [today + timedelta(days=i) for i in range(7)]

    def display_tasks_for_date(date):
        tasks = todo_list.get_tasks(date.strftime("%Y-%m-%d"))
        return ft.Column([ft.Text(f"{task[1]}") for task in tasks])

    def build_calendar():
        days = get_7_day_range()
        return ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(day.strftime("%A, %b %d")),
                        display_tasks_for_date(day),
                    ]
                )
                for day in days
            ]
        )

    return ft.View(
        "/calendar",
        [
            ft.AppBar(title=ft.Text("7-Day Outlook")),
            build_calendar(),
        ],
    )