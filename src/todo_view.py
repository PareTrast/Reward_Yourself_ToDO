# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\todo_view.py
import datetime
'''import os
import sys'''
import requests
from requests.exceptions import RequestException, HTTPError, Timeout
import json
import config_loader
from supabase import Client

# Import Supabase/PostgREST exceptions if needed for specific checks
from postgrest import APIError as PostgrestAPIError
from gotrue.errors import AuthApiError
import traceback

# Get config values from the loader
SUPABASE_URL = config_loader.get_supabase_url()
SUPABASE_KEY = config_loader.get_supabase_anon_key()  # This is the Anon Key

# Check if loading failed
if config_loader.CONFIG_ERROR:
    print(
        f"ToDoList - Warning: Configuration error detected: {config_loader.CONFIG_ERROR}"
    )
    # Handle error appropriately - maybe raise an exception or disable functionality

# --- Constants ---
MEDALS_PER_TASK = 1  # Define how many medals a task is worth

# Keep the print statement for debugging if needed
print(
    f"ToDoList - Using API Key (Anon): {'*' * (len(SUPABASE_KEY) - 5) + SUPABASE_KEY[-5:] if SUPABASE_KEY else 'Not Set'}"
)
print(f"ToDoList - Using API URL: {SUPABASE_URL}")


class ToDoList:
    # --- Modify __init__ (Remove user_manager) ---
    def __init__(
        self,
        username,
        is_web_environment,
        supabase_client: Client,
        # user_manager: UserManager, # Removed user_manager parameter
    ):
        self.username = username
        self.is_web_environment = is_web_environment
        self.api_url = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else None
        self.rpc_url = (
            f"{SUPABASE_URL}/rest/v1/rpc" if SUPABASE_URL else None
        )  # Add RPC URL
        self.access_token = None
        self.user_id = None  # Will be set later
        self.refresh_token = None
        self.session = requests.Session()
        self.supabase_client = supabase_client
        # self.user_manager = user_manager # Removed user_manager storage

        if not self.api_url:
            print("ToDoList Error: API URL is not configured. Check config.json.")
        if not self.rpc_url:
            print("ToDoList Error: RPC URL is not configured. Check config.json.")
        if not self.supabase_client:
            print("ToDoList Error: Supabase client was not provided.")
        # --- Remove check for user_manager ---
        # if not self.user_manager:
        #     print("ToDoList Error: UserManager instance was not provided.")
        # --- End remove ---

    # --- End modification ---

    def set_access_token(self, access_token, refresh_token=None):
        """Sets the access token for API calls and updates the session headers."""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token

        if not SUPABASE_KEY:  # Check Anon Key from config_loader
            print(
                "ToDoList Error: Supabase Anon Key not configured. Cannot set auth headers."
            )
            return

        # Update requests session headers (for direct REST calls via _make_request)
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "apikey": SUPABASE_KEY,  # Use Anon key from config_loader
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
        )
        print("Access token set in requests session headers.")

        # ALSO set session in the supabase-py client instance
        if self.supabase_client and self.access_token and self.refresh_token:
            try:
                self.supabase_client.auth.set_session(
                    self.access_token, self.refresh_token
                )
                print("Session set in supabase-py client.")
            except Exception as e:
                print(f"Error setting session in supabase-py client: {e}")
        elif not self.supabase_client:
            print("Warning: supabase_client not available in set_access_token.")

    def _make_request(self, method, endpoint, base_url=None, **kwargs):
        """Helper method for making synchronous requests (Data or RPC) via requests library."""
        if config_loader.CONFIG_ERROR:
            print(
                f"Error: Cannot make request due to config error: {config_loader.CONFIG_ERROR}"
            )
            return None

        current_base_url = base_url if base_url else self.api_url
        if not current_base_url:
            print(f"Error: Base URL ({'RPC' if base_url else 'Data'}) not configured.")
            return None

        if not self.access_token:
            print("Error: Access token not set for API call.")
            return None

        url = f"{current_base_url}/{endpoint}"
        # Use headers from self.session which are set in set_access_token
        headers = self.session.headers

        print(f"Making {method} request to: {url}")
        try:
            response = requests.request(
                method, url, headers=headers, timeout=15, **kwargs
            )  # Use requests.request
            print(f"Response Status: {response.status_code}")

            response.raise_for_status()  # Check for HTTP errors first

            # Handle success based on status code and method
            if response.status_code == 204:  # No Content (e.g., DELETE)
                return True  # Return True for successful DELETE
            # Check for empty body even on 200/201
            if not response.content:
                if method == "GET":
                    return []  # Empty list for GET
                # For POST RPC, 200 OK with empty body might be success
                if method == "POST" and endpoint.startswith(
                    "increment_user_medal_count"
                ):  # Check specific RPC endpoint name
                    # Our RPC should return JSON, so empty body is unexpected here
                    print(f"Warning: RPC {endpoint} returned 200 OK but empty body.")
                    return None  # Indicate potential issue
                # For other POSTs (like history insert), empty body on 201 might be okay
                if method == "POST" and response.status_code == 201:
                    print(
                        f"Warning: POST to {endpoint} returned 201 Created but empty body."
                    )
                    # Let's assume success if status is 201, but log it.
                    # Supabase often returns the created object, so empty is unusual.
                    return (
                        {}
                    )  # Return an empty dict to indicate success but no data returned
                return True  # Assume success for other POSTs with empty body? Or handle specific cases.
            # If body is not empty, try parsing JSON
            return response.json()

        except HTTPError as e:
            print(
                f"HTTP Error during {method} {url}: {e.response.status_code} - {e.response.text}"
            )
            if e.response.status_code == 401:
                print("Authorization Error (401): Token might be expired or invalid.")
            return None
        except requests.exceptions.Timeout:
            print(f"Timeout Error during {method} {url}")
            return None
        except RequestException as e:
            print(f"Network Error during {method} {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(
                f"JSON Decode Error during {method} {url}: {e} - Response: {response.text[:200]}"
            )
            return None
        except Exception as e:
            print(f"Unexpected error during {method} {url}: {e}")
            return None

    # --- Modified get_medal_count (More Robust Error Handling) ---
    def get_medal_count(self):
        """Fetches the current user's medal count from the public.user_profiles table.
        Creates a profile with 0 medals if it doesn't exist."""
        print("--- get_medal_count called ---")
        if not self.supabase_client:
            print("Error: Supabase client not available for get_medal_count.")
            return None

        if (
            not self.supabase_client.supabase_url
            or not self.supabase_client.supabase_key
        ):
            print("Error: Supabase client URL or Key is missing before query.")
            return None

        current_user_id = None
        profile_data = None  # To store fetched profile data

        try:
            # --- Get User ID ---
            current_user_id = self.user_id
            if not current_user_id:
                print("get_medal_count: User ID not cached, fetching...")
                try:
                    user_response = self.supabase_client.auth.get_user()
                    if not (user_response and user_response.user):
                        print("get_medal_count: Could not get current user session.")
                        return None
                    current_user_id = user_response.user.id
                    self.user_id = current_user_id
                except (AuthApiError, RequestException, Exception) as auth_e:
                    print(f"get_medal_count: Error fetching user ID: {auth_e}")
                    traceback.print_exc()
                    return None
            print(f"get_medal_count: Current User ID: {current_user_id}")

            # --- Attempt to Fetch Profile ---
            print(f"Querying 'user_profiles' table for id: {current_user_id}")
            response = None  # Initialize response
            try:
                # Build the query first
                query = (
                    self.supabase_client.table("user_profiles")
                    .select("medal_count")
                    .eq("id", current_user_id)
                    .maybe_single()
                )
                # Execute the query
                print("Executing profile fetch query...")
                response = query.execute()
                print("Profile fetch query executed.")

            except (RequestException, Timeout) as network_err:
                print(f"Network Error during profile query execution: {network_err}")
                traceback.print_exc()
                return None
            except PostgrestAPIError as pg_err:
                print(f"PostgREST API Error during profile query: {pg_err}")
                traceback.print_exc()
                return None
            except Exception as exec_err:
                print(f"Unexpected Error during profile query execution: {exec_err}")
                traceback.print_exc()
                return None

            # --- Check Response Object ---
            if response is None:
                # This is the persistent strange issue
                print("Error: Supabase query execution resulted in None object.")
                return None

            # --- Process Response Data ---
            profile_data = response.data  # Store data (can be None if no profile found)
            print(f"Profile query response data: {profile_data}")

            if profile_data is not None:
                # Profile Found
                count = profile_data.get("medal_count", 0)
                print(f"Fetched medal count from profile: {count}")
                try:
                    return int(count)
                except (ValueError, TypeError):
                    print(
                        f"Warning: Invalid medal count '{count}' in profile. Returning 0."
                    )
                    return 0
            else:
                # --- Profile Not Found - Attempt to Create ---
                print(
                    f"No profile found for user ID {current_user_id}. Attempting to create one."
                )
                try:
                    profile_insert_data = {"id": current_user_id, "medal_count": 0}
                    print(f"Inserting profile data: {profile_insert_data}")
                    insert_response = (
                        self.supabase_client.table("user_profiles")
                        .insert(profile_insert_data)
                        .execute()
                    )

                    if insert_response is None:
                        print(
                            "Error: Profile insert execution resulted in None object."
                        )
                        return None  # Failed to insert

                    print(f"Profile insert response data: {insert_response.data}")
                    if insert_response.data:
                        print(
                            f"Successfully inserted default profile for user {current_user_id}."
                        )
                        return 0  # Return 0 as the initial count
                    else:
                        # Check for specific errors if data is empty/None
                        error_info = getattr(insert_response, "error", None)
                        status_code = getattr(insert_response, "status_code", None)
                        print(
                            f"Failed to insert default profile (no data returned). Status: {status_code}, Error: {error_info}"
                        )
                        return None

                except PostgrestAPIError as insert_pg_err:
                    print(f"PostgREST Error inserting default profile: {insert_pg_err}")
                    if (
                        'duplicate key value violates unique constraint "user_profiles_pkey"'
                        in str(insert_pg_err)
                    ):
                        print(
                            "Profile likely created concurrently. Assuming 0 medals for now."
                        )
                        return 0
                    else:
                        traceback.print_exc()
                        return None
                except Exception as insert_e:
                    print(f"Unexpected Error inserting default profile: {insert_e}")
                    traceback.print_exc()
                    return None
                # --- End Profile Creation Attempt ---

        except Exception as e:
            # Catch any other unexpected errors in the outer logic
            print(f"Outer error in get_medal_count: {e}")
            traceback.print_exc()
            return None

    # --- End modification ---

    def _update_medal_count_rpc(self, amount_to_add):
        """Updates the user's medal count using the RPC function (which now targets user_profiles).
        Returns the new count on success, None on failure."""
        print(f"--- _update_medal_count_rpc called with amount: {amount_to_add} ---")
        if not self.rpc_url:
            print("Error: Cannot update medal count, RPC URL not set.")
            return None
        if not self.access_token:
            print("Error: Cannot update medal count, access token not set.")
            return None

        endpoint = "increment_user_medal_count"  # This function name remains the same
        payload = {"amount_param": amount_to_add}
        print(f"Calling RPC: {endpoint} with payload: {payload}")

        # Use _make_request which uses the standard REST endpoint for RPC
        response_data = self._make_request(
            "POST", endpoint, base_url=self.rpc_url, json=payload
        )
        print(f"RPC Response Data: {response_data}")  # Log the raw response

        # Check for success more carefully
        if response_data is None:
            print(
                "Failed to update medal count via RPC: No response from _make_request."
            )
            return None
        elif isinstance(response_data, dict) and response_data.get("success"):
            new_count = response_data.get("new_medal_count")
            # Validate new_count type
            if isinstance(new_count, int):
                print(
                    f"Successfully updated medal count via RPC. New count: {new_count}"
                )
                return new_count
            else:
                print(
                    f"RPC success=true, but new_medal_count is not an integer: {new_count}"
                )
                return None  # Treat invalid count as failure
        else:
            # Handle cases where response_data is not a dict or success is not true
            error_msg = "Unknown RPC error or invalid response format"
            if isinstance(response_data, dict):
                error_msg = response_data.get("error", error_msg)
            print(f"Failed to update medal count via RPC: {error_msg}")
            if "permission denied" in str(error_msg).lower():
                print(
                    "Hint: Check if EXECUTE permission was granted to the 'authenticated' role for the function, or if RLS prevents the update."
                )
            return None

    def get_all_tasks(self):
        """Fetches all tasks for the user (synchronous)."""
        endpoint = "tasks"
        # RLS on 'tasks' table should filter by user_id automatically
        params = {"select": "*"}
        data = self._make_request("GET", endpoint, params=params)
        return data if isinstance(data, list) else []

    def add_new_task(self, task_data):
        """Adds a new task for the user (synchronous). Relies on RLS for user_id."""
        endpoint = "tasks"
        if not self.username:
            print("Error: Username not set. Cannot add task.")
            return None
        # Ensure username is part of the data if your table/RLS needs it
        task_data["username"] = self.username

        # --- Remove explicit user_id ---
        # We rely on RLS (auth.uid()) to set the user association implicitly
        # if self.user_id:
        #     task_data["user_id"] = self.user_id
        # --- End Removal ---

        print(f"Sending task data to API (RLS handles user_id): {task_data}")
        response_data = self._make_request("POST", endpoint, json=task_data)
        if (
            response_data is not None
        ):  # Check if response is not None (success or empty dict/list)
            print("Task added successfully.")
            return response_data  # Return the actual response (might be {} or the created object)
        else:
            print("Failed to add task.")
            return None

    def get_all_rewards(self):
        """Fetches all rewards for the user (synchronous)."""
        endpoint = "rewards"
        # RLS on 'rewards' table should filter by user_id automatically
        params = {"select": "*"}
        data = self._make_request("GET", endpoint, params=params)
        print(f"Fetched Rewards from API: {data}")
        return data if isinstance(data, list) else []

    def add_new_reward(self, reward_data):
        """Adds a new reward for the user (synchronous). Relies on RLS for user_id."""
        endpoint = "rewards"
        if not self.username:
            print("Error: Username not set. Cannot add reward.")
            return None
        # Ensure username is part of the data if your table/RLS needs it
        reward_data["username"] = self.username

        # --- Remove explicit user_id ---
        # We rely on RLS (auth.uid()) to set the user association implicitly
        # if self.user_id:
        #     reward_data["user_id"] = self.user_id
        # --- End Removal ---

        print(f"Sending reward data to API (RLS handles user_id): {reward_data}")
        response_data = self._make_request("POST", endpoint, json=reward_data)
        if response_data is not None:  # Check if response is not None
            print("Reward added successfully.")
            return response_data  # Return the actual response
        else:
            print("Failed to add reward.")
            return None

    def mark_task_done(self, task_id, task_name):
        """Marks a task as done, adds to history, and increments medals.
        Returns (True, new_medal_count) on success, (False, None) on failure."""
        print(f"--- mark_task_done called for task ID: {task_id} ---")

        # 1. Add to task history
        history_data = {
            "description": task_name,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        history_endpoint = "task_history"
        if self.username:
            history_data["username"] = self.username
        # user_id is likely handled by RLS, but include if needed by table/policy
        if self.user_id:
            history_data["user_id"] = self.user_id

        print(f"Step 1: Sending task history data: {history_data}")
        history_response = self._make_request(
            "POST", history_endpoint, json=history_data
        )
        if history_response is None:
            print("Error adding task to history. Aborting task completion.")
            return False, None

        print("Step 1: Task history added successfully.")

        # 2. Delete the task
        task_endpoint = f"tasks?id=eq.{task_id}"
        print(f"Step 2: Deleting task: {task_endpoint}")
        delete_success = self._make_request("DELETE", task_endpoint)
        if not delete_success:  # Expects True on success (204)
            print(f"Error deleting task {task_id} after adding to history.")
            return False, None

        print("Step 2: Task deleted successfully.")

        # 3. Increment medal count (using RPC which now targets user_profiles)
        print(f"Step 3: Attempting to increment medals by {MEDALS_PER_TASK}")
        new_medal_count = self._update_medal_count_rpc(MEDALS_PER_TASK)
        print(f"Step 3 Result: new_medal_count = {new_medal_count}")

        if new_medal_count is None:
            print(
                f"Warning: Task {task_id} completed and deleted, but failed to update medal count."
            )
            return True, None  # Task done, but medal count update failed
        else:
            print(f"Task {task_id} processing finished successfully.")
            return True, new_medal_count

    # --- Modified claim_reward (Add Logging) ---
    def claim_reward(self, reward_id, reward_name, reward_cost):
        """Claims a reward, adds to history, and decrements medals.
        Returns (True, new_medal_count) on success, (False, error_message) on failure.
        """
        print(
            f"--- claim_reward started: {reward_name}, Cost: {reward_cost} ---"
        )  # Modified log
        # 0. Check funds
        current_medals = self.get_medal_count()
        print(f"claim_reward: Current medals check: {current_medals}")  # Added log
        if current_medals is None:
            print("claim_reward: Error fetching current medal count.")
            return False, "Error fetching medal count."
        if reward_cost > current_medals:
            msg = f"claim_reward: Not enough medals ({current_medals}) to claim reward costing {reward_cost}."
            print(msg)
            return False, msg
        print("claim_reward: Medal check passed.")  # Added log

        # 1. Add to reward history
        history_data = {
            "description": reward_name,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cost": reward_cost,
        }
        history_endpoint = "reward_history"
        if self.username:
            history_data["username"] = self.username
        # user_id is likely handled by RLS, include if needed
        if self.user_id:
            history_data["user_id"] = self.user_id

        print(f"claim_reward: Step 1 - Sending reward history data: {history_data}")
        history_response = self._make_request(
            "POST", history_endpoint, json=history_data
        )
        # --- Add detailed logging for history response ---
        print(f"claim_reward: Step 1 - History insert response: {history_response}")
        # --- End added log ---
        if history_response is None:  # Check for None explicitly
            print("claim_reward: Error adding reward to history. Aborting.")
            return False, "Failed to record reward in history."
        # If _make_request returns {} on success (201 with empty body), treat as success
        print("claim_reward: Step 1 - History insert successful.")  # Added log

        # 2. Delete the reward
        reward_endpoint = f"rewards?id=eq.{reward_id}"
        print(f"claim_reward: Step 2 - Deleting reward: {reward_endpoint}")
        delete_success = self._make_request("DELETE", reward_endpoint)
        # --- Add detailed logging for delete response ---
        print(
            f"claim_reward: Step 2 - Reward delete response (True means success): {delete_success}"
        )
        # --- End added log ---
        if not delete_success:  # _make_request returns True on successful DELETE (204)
            print(f"claim_reward: Error deleting reward {reward_id}. Aborting.")
            # Consider rolling back history entry
            return False, "Failed to remove reward after claiming."
        print(f"claim_reward: Step 2 - Reward delete successful.")  # Added log

        # 3. Decrement medal count (using RPC)
        print(f"claim_reward: Step 3 - Decrementing medals by {reward_cost}")
        new_medal_count = self._update_medal_count_rpc(
            -reward_cost
        )  # This already logs internally
        # --- Add detailed logging for RPC result ---
        print(f"claim_reward: Step 3 - RPC result (new_medal_count): {new_medal_count}")
        # --- End added log ---

        if new_medal_count is None:
            print(
                f"claim_reward: Warning - Reward claimed/deleted, but medal update failed."
            )
            return True, None  # Partial success
        else:
            print(
                f"claim_reward: Full success - Reward claimed. New count: {new_medal_count}"
            )
            return True, new_medal_count  # Full success

    # --- End Modification ---

    def get_task_history(self):
        """Fetches the task history for the user (synchronous)."""
        endpoint = "task_history"
        # RLS on 'task_history' table should filter by user_id automatically
        params = {"select": "*", "order": "timestamp.desc"}
        data = self._make_request("GET", endpoint, params=params)
        return data if isinstance(data, list) else []

    def get_reward_history(self):
        """Fetches the reward history for the user (synchronous)."""
        endpoint = "reward_history"
        # RLS on 'reward_history' table should filter by user_id automatically
        params = {"select": "*", "order": "timestamp.desc"}
        data = self._make_request("GET", endpoint, params=params)
        return data if isinstance(data, list) else []
