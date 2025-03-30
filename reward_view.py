import flet as ft
from todo_view import ToDoList

def reward_view(page: ft.Page, todo_list: ToDoList):
    reward_input = ft.TextField(label="New Reward", expand=True)
    medal_cost_input = ft.TextField(
        label="Medal Cost", keyboard_type=ft.KeyboardType.NUMBER, expand=True
    )
    medal_count = ft.Text(f"You have {todo_list.medals} medals.")
    reward_list = ft.Column()

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

    update_reward_list()

    return ft.View(
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
                                                "Add Reward", on_click=add_reward
                                            ),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Container(content=reward_list, expand=True),
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