# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\reward_view.py
import flet as ft
from todo_view import ToDoList
import os


# --- Update function signature ---
def reward_view(
    page: ft.Page, todo_list: ToDoList, trigger_main_medal_update: callable
):
    # --- End modification ---

    reward_list_view = ft.ListView(
        expand=True, spacing=10, padding=20, auto_scroll=True
    )
    reward_input = ft.TextField(label="New Reward", expand=True)
    medal_cost_input = ft.TextField(
        label="Medal Cost",
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"[0-9]", replacement_string=""
        ),
    )

    # --- Modify refresh_reward_list ---
    def refresh_reward_list():
        """Refreshes the list of rewards."""
        reward_list_view.controls.clear()
        if not todo_list:
            reward_list_view.controls.append(ft.Text("Error: Not logged in."))
            # page.update() # Let caller handle update
            return

        print("Refreshing reward list...")
        # No need to fetch medals just for button state anymore

        rewards = todo_list.get_all_rewards()

        if rewards:
            for reward in rewards:
                reward_id, reward_name, cost = (
                    reward.get("id"),
                    reward.get("reward", "Unnamed"),
                    reward.get("medal_cost", 0),
                )
                if reward_id is None:
                    continue
                reward_list_view.controls.append(
                    ft.Row(
                        [
                            ft.Text(
                                f"{reward_name} - {cost} medals",
                                expand=True,
                                tooltip=reward_name,
                            ),
                            ft.ElevatedButton(
                                "Claim",
                                tooltip=f"Claim for {cost} medals",
                                on_click=lambda _, rid=reward_id, rname=reward_name, rcost=cost: claim_reward(
                                    rid, rname, rcost
                                ),
                                # --- Remove disabled logic ---
                                # disabled=(cost > effective_medals), # ALWAYS ENABLED NOW
                                # --- End Remove ---
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )
        else:
            reward_list_view.controls.append(ft.Text("No rewards available."))
        # Don't call page.update() here, let the caller handle it
        # page.update()

    # --- End modification ---

    def add_reward(e):
        """Handles adding a new reward."""
        if todo_list:
            reward_text = reward_input.value.strip()
            cost_text = medal_cost_input.value.strip()
            if reward_text and cost_text.isdigit():
                cost = int(cost_text)
                new_reward_data = {"reward": reward_text, "medal_cost": cost}
                added_reward = todo_list.add_new_reward(new_reward_data)
                if added_reward:
                    reward_input.value = ""
                    medal_cost_input.value = ""
                    reward_input.focus()
                    refresh_reward_list()  # Refresh list
                    page.snack_bar = ft.SnackBar(ft.Text("Reward added!"))
                    page.snack_bar.open = True
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Error adding reward."))
                    page.snack_bar.open = True
                page.update()  # Update page after add action
            else:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Please enter a valid reward and numeric medal cost.")
                )
                page.snack_bar.open = True
                if not reward_text:
                    reward_input.focus()
                else:
                    medal_cost_input.focus()
                page.update()  # Update page for validation error
        else:
            print("Error: todo_list not available in add_reward.")

    # --- Modify claim_reward ---
    def claim_reward(reward_id, reward_name, reward_cost):
        """Event handler for the claim button."""
        print(
            f"Attempting to claim reward via UI: {reward_name} (ID: {reward_id}), Cost: {reward_cost}"
        )
        if todo_list:
            # Backend handles the actual medal check now
            success, result_data = todo_list.claim_reward(
                reward_id, reward_name, reward_cost
            )

            message = ""
            if success:
                new_count = (
                    result_data  # This is the new medal count (or None if RPC failed)
                )
                message = f"Reward '{reward_name}' claimed!"
                if new_count is None:
                    message = f"Reward '{reward_name}' claimed! (Medal update may have failed, refreshing count...)"
                print(f"Claim successful: {message}")
                refresh_reward_list()  # Refresh list only on success
            else:
                error_message = result_data  # This is the error message
                message = f"Claim failed: {error_message}"
                print(message)
                # Don't refresh list on failure

            page.snack_bar = ft.SnackBar(ft.Text(message))
            page.snack_bar.open = True

            # --- Trigger update of the main medal display ---
            trigger_main_medal_update()  # Call the function passed from main.py
            # --- End modification ---

            page.update()  # Show snackbar and update list/display changes
        else:
            print("Error: todo_list object not available when trying to claim reward.")
            page.snack_bar = ft.SnackBar(ft.Text("Error: Not logged in."))
            page.snack_bar.open = True
            page.update()

    # --- End modification ---

    add_reward_button = ft.ElevatedButton("Add Reward", on_click=add_reward)

    # --- Initial population (No medal fetch needed here anymore) ---
    refresh_reward_list()
    # --- End modification ---

    return ft.View(
        "/rewards",
        [
            ft.AppBar(
                title=ft.Text("Rewards"),
                leading=ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    tooltip="Back to Tasks",
                    on_click=lambda _: page.go("/"),
                ),
                # --- Remove local medal count display from actions ---
                actions=[],
                # --- End modification ---
            ),
            ft.Column(
                [
                    ft.Row(
                        [reward_input, medal_cost_input, add_reward_button],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    ft.Text(
                        "Available Rewards", style=ft.TextThemeStyle.HEADLINE_SMALL
                    ),
                    reward_list_view,
                ],
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            # bottom_appbar should be added by main.py's route_change
        ],
        padding=10,
    )
