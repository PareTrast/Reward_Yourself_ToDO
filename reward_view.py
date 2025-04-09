# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\reward_view.py
import flet as ft
from todo_view import ToDoList
import httpx
from dotenv import load_dotenv
import os
import asyncio  # Keep asyncio for create_task if needed, but page.run_task is preferred

load_dotenv()

SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # Replace with your actual Supabase key


def reward_view(page: ft.Page, todo_list: ToDoList):
    reward_list = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True)

    async def refresh_reward_list():
        reward_list.controls.clear()
        if todo_list:
            rewards = await todo_list.get_all_rewards()
            print(f"Fetched Rewards: {rewards}")  # Debugging
            for reward in rewards:
                reward_id = reward["id"]
                reward_name = reward["reward"]
                cost = reward["medal_cost"]
                print(
                    f"Processing reward: {reward_name} (ID: {reward_id})"
                )  # Debugging

                # Define the handler function separately for clarity and proper async handling
                async def handle_claim_change(e, rid=reward_id, rname=reward_name):
                    # Only claim if the checkbox is being checked (value becomes True)
                    if e.control.value:
                        print(
                            f"Checkbox checked for reward: {rname} (ID: {rid})"
                        )  # Debugging
                        await claim_reward(rid, rname)
                        # The refresh_reward_list called by claim_reward will update the UI
                        # No need to manually set value back to False here if refresh works
                    else:
                        print(
                            f"Checkbox unchecked for reward: {rname} (ID: {rid})"
                        )  # Debugging

                reward_list.controls.append(
                    ft.Checkbox(
                        label=f"{reward_name} - {cost} medals",
                        value=False,  # Start unchecked
                        # Use page.run_task to correctly schedule the async handler
                        on_change=lambda e, rid=reward_id, rname=reward_name: page.run_task(
                            handle_claim_change, e, rid, rname
                        ),
                    )
                )
            page.update()

    async def add_reward(e):
        if todo_list:
            if reward_input.value and medal_cost_input.value.isdigit():
                print(f"Reward Input: {reward_input.value}")  # Debugging
                print(f"Medal Cost Input: {medal_cost_input.value}")  # Debugging
                await todo_list.add_new_reward(
                    {
                        "username": todo_list.username,
                        "reward": reward_input.value,
                        "medal_cost": int(medal_cost_input.value),
                    }
                )
                print("add_new_reward called successfully!")  # Debugging
                reward_input.value = ""
                medal_cost_input.value = ""
                await refresh_reward_list()
            else:
                print("Invalid input for reward or medal cost.")  # Debugging
                page.snack_bar = ft.SnackBar(
                    ft.Text("Please enter a valid reward and medal cost.")
                )
                page.snack_bar.open = True
                page.update()

    # This function now delegates the work to the ToDoList object's method
    async def claim_reward(reward_id, reward_name):
        print(
            f"Attempting to claim reward via todo_list: {reward_name} (ID: {reward_id})"
        )  # Debugging
        if todo_list:
            try:
                # *** This is the key change: Call the method on todo_list ***
                await todo_list.claim_reward(reward_id, reward_name)
                print(
                    f"todo_list.claim_reward likely succeeded for {reward_name}"
                )  # Debugging
                # Refresh the list to show the reward is gone
                await refresh_reward_list()
            except Exception as e:
                # Log the error appropriately
                print(
                    f"An error occurred while claiming reward '{reward_name}' (ID: {reward_id}): {e}"
                )
                # Show an error message to the user
                page.snack_bar = ft.SnackBar(ft.Text(f"Error claiming reward: {e}"))
                page.snack_bar.open = True
                # You might want to refresh the list even on error, or maybe not.
                # await refresh_reward_list()
                page.update()  # Update to show the snackbar
        else:
            print("Error: todo_list object not available when trying to claim reward.")
            page.snack_bar = ft.SnackBar(
                ft.Text("Error: Cannot claim reward. System error.")
            )
            page.snack_bar.open = True
            page.update()

    reward_input = ft.TextField(label="New Reward", expand=True)
    medal_cost_input = ft.TextField(
        label="Medal Cost", keyboard_type=ft.KeyboardType.NUMBER, expand=True
    )
    add_reward_button = ft.ElevatedButton("Add Reward", on_click=add_reward)

    # Initial population of the list
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
                    reward_list,  # The ListView containing checkboxes
                ],
                expand=True,
            ),
        ],
    )
