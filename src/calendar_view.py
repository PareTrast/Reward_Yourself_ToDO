import flet as ft
import arrow

def build_calendar(page: ft.Page):
    today  = arrow.now()
    days = []
    for i in range(7):
        date = today.shift(days=-today.weekday()+i)
        day_name = date.format('dddd') # this is the day name. e.g. Sunday
        day_number = date.format('DD') # this id the day's number. e.g. 15
        is_today = date == today
        days.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(day_name, size=12, weight="bold", ),
                        ft.Text(day_number, size=24, weight="bold", color=ft.Colors.RED_200 if is_today else ft.Colors.BLUE_200),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    
                ),
                expand=True,
                height = 100,
                border = ft.border.all(1, ft.Colors.GREY),
                border_radius = ft.border_radius.all(5),
                padding=10,
            )
            )
    return ft.Row(days, alignment=ft.MainAxisAlignment.SPACE_EVENLY, expand=True)
