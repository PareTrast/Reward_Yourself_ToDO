import flet as ft
from todo_view import ToDoList
import sys

# Conditional import based on environment
if "pyodide" in sys.modules:  # Running in a Pyodide (web) environment
    from pyodide.http import pyfetch  # type: ignore
else:  # Running in a non-web environment
    import requests


def reward_view(page: ft.Page, todo_list: ToDoList):
    reward_list = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)

    async def refresh_reward_list():
        reward_list.controls.clear()
        if todo_list:
            try:
                if "pyodide" in sys.modules:  # Web environment
                    # Fetch rewards using pyodide-http
                    response = await pyfetch(
                        url=f"{todo_list.api_url}/rewards",
                        method="GET",
                        headers={
                            "Authorization": f"Bearer {todo_list.access_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    rewards = await response.json()
                else:  # Non-web environment
                    # Fetch rewards using requests
                    response = requests.get(
                        f"{todo_list.api_url}/rewards",
                        headers={
                            "Authorization": f"Bearer {todo_list.access_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    response.raise_for_status()
                    rewards = response.json()

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
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
        page.update()

    async def add_reward(e):
        if todo_list:
            try:
                if "pyodide" in sys.modules:  # Web environment
                    # Add a new reward using pyodide-http
                    await pyfetch(
                        url=f"{todo_list.api_url}/rewards",
                        method="POST",
                        headers={
                            "Authorization": f"Bearer {todo_list.access_token}",
                            "Content-Type": "application/json",
                        },
                        body={
                            "username": todo_list.username,
                            "reward": reward_input.value,
                            "medal_cost": int(medal_cost_input.value),
                        },
                    )
                else:  # Non-web environment
                    # Add a new reward using requests
                    response = requests.post(
                        f"{todo_list.api_url}/rewards",
                        json={
                            "username": todo_list.username,
                            "reward": reward_input.value,
                            "medal_cost": int(medal_cost_input.value),
                        },
                        headers={
                            "Authorization": f"Bearer {todo_list.access_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    response.raise_for_status()

                reward_input.value = ""
                medal_cost_input.value = ""
                await refresh_reward_list()
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    async def claim_reward(reward_id, reward_name):
        try:
            if "pyodide" in sys.modules:  # Web environment
                # Claim a reward using pyodide-http
                await pyfetch(
                    url=f"{todo_list.api_url}/rewards/{reward_id}/claim",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {todo_list.access_token}",
                        "Content-Type": "application/json",
                    },
                )
            else:  # Non-web environment
                # Claim a reward using requests
                response = requests.post(
                    f"{todo_list.api_url}/rewards/{reward_id}/claim",
                    headers={
                        "Authorization": f"Bearer {todo_list.access_token}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

            await refresh_reward_list()
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
