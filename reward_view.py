import flet as ft
from todo_view import ToDoList
from postgrest import APIError


def reward_view(page: ft.Page, todo_list: ToDoList):
    reward_list = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)

    async def refresh_reward_list():
        reward_list.controls.clear()
        if todo_list:
            try:
                rewards = await todo_list.get_all_rewards()
                for reward in rewards:
                    reward_id = reward["id"]
                    reward_name = reward["reward"]
                    cost = reward["medal_cost"]
                    reward_list.controls.append(
                        ft.ListTile(
                            leading=ft.Checkbox(
                                value=False,
                                on_change=lambda e, reward_id=reward_id, reward_name=reward_name: page.run_task(
                                    claim_reward, reward_id, reward_name
                                ),
                            ),
                            title=ft.Text(reward_name),
                            subtitle=ft.Text(f"{cost} medals"),
                        )
                    )
            except APIError as e:
                print(f"Supabase API Error: {e}")
                print(f"Error details: {e.details}")
                print(f"Error hint: {e.hint}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        page.update()

    async def add_reward(e):
        if todo_list:
            try:
                await todo_list.add_new_reward(
                    {
                        "username": todo_list.username,
                        "reward": reward_input.value,
                        "medal_cost": int(medal_cost_input.value),
                    }
                )
                reward_input.value = ""
                medal_cost_input.value = ""
                await refresh_reward_list()
            except APIError as e:
                print(f"Supabase API Error: {e}")
                print(f"Error details: {e.details}")
                print(f"Error hint: {e.hint}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    async def claim_reward(reward_id, reward_name):
        try:
            await todo_list.claim_reward(reward_id, reward_name)
            await refresh_reward_list()
        except APIError as e:
            print(f"Supabase API Error: {e}")
            print(f"Error details: {e.details}")
            print(f"Error hint: {e.hint}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    reward_input = ft.TextField(label="New Reward", expand=True)
    medal_cost_input = ft.TextField(
        label="Medal Cost", keyboard_type=ft.KeyboardType.NUMBER, expand=True
    )
    add_reward_button = ft.ElevatedButton("Add Reward", on_click=add_reward)

    page.run_task(refresh_reward_list)

    return ft.View(
        "/rewards",
        [
            ft.AppBar(
                title=ft.Text("Rewards"),
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")
                ),
            ),
            ft.Column(
                [
                    ft.Row(
                        [reward_input, medal_cost_input, add_reward_button],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    reward_list,
                ],
                expand=True,
            ),
        ],
    )
