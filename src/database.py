# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\database.py
import os
import json
from supabase import create_client, Client  # Changed import
from supabase.lib.client_options import ClientOptions
import requests  # Import requests for potential future use if needed directly

# Load configuration from config.json (Keep this part)
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    SUPABASE_URL = config.get("SUPABASE_URL")
    SUPABASE_KEY = config.get("SUPABASE_KEY")
except FileNotFoundError:
    print("Error: config.json not found. Please ensure it exists.")
    # Consider exiting or raising a more specific error if config is critical
    SUPABASE_URL = None
    SUPABASE_KEY = None
except json.JSONDecodeError:
    print("Error: Could not decode config.json. Please check its format.")
    SUPABASE_URL = None
    SUPABASE_KEY = None


class Database:
    SESSION_FILE = "session.json"

    def __init__(self, is_web_environment=False):
        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not set or loaded from config.json.")
        if not SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is not set or loaded from config.json.")

        # Use the synchronous Client
        self.supabase: Client = None
        self.access_token = None
        self.refresh_token = None
        self.is_web_environment = is_web_environment
        self.create_supabase_client()  # Initialize client in constructor

    # Make this synchronous
    def create_supabase_client(self):
        # Use create_client (synchronous)
        self.supabase: Client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            options=ClientOptions(
                # persist_session=False might not be needed for sync client
                # auto_refresh_token=True is generally useful
                auto_refresh_token=True
            ),
        )
        print("Synchronous Supabase client created.")

    # Make this synchronous
    def set_access_token(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

        # Use the synchronous set_session
        # Note: The sync client often handles sessions internally based on login,
        # but explicitly setting it might still be needed depending on your flow.
        # Check supabase-py sync client docs if issues arise.
        try:
            # The sync client might automatically manage the session after sign_in
            # If you need to manually set it (e.g., after loading from file), use:
            self.supabase.auth.set_session(access_token, refresh_token)
            print("Session set in Supabase client.")
        except Exception as e:
            print(f"Error setting session in Supabase client: {e}")
            # Decide how to handle this - maybe re-authentication is needed

        self.save_session(access_token, refresh_token)

    # save_session and load_session remain synchronous
    def save_session(self, access_token, refresh_token):
        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        try:
            with open(self.SESSION_FILE, "w") as f:
                json.dump(session_data, f)
        except Exception as e:
            print(f"Error saving session to {self.SESSION_FILE}: {e}")

    def load_session(self):
        try:
            with open(self.SESSION_FILE, "r") as f:
                session_data = json.load(f)
                # Optionally set the session in the client upon loading
                # if self.supabase and session_data:
                #    self.set_access_token(session_data.get("access_token"), session_data.get("refresh_token"))
                return session_data
        except FileNotFoundError:
            print(f"{self.SESSION_FILE} not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.SESSION_FILE}.")
            return None
        except Exception as e:
            print(f"Error loading session from {self.SESSION_FILE}: {e}")
            return None

    # _handle_response remains synchronous
    def _handle_response(self, response):
        # Sync client responses might differ slightly, adjust if needed
        # Often, sync methods raise exceptions on errors directly.
        # Check the structure of 'response' from sync calls.
        # Assuming it still has a 'data' attribute on success:
        if hasattr(response, "data"):
            return response.data
        # If errors are raised as exceptions, the try/except blocks handle them.
        # If errors are returned in the response object, check for that:
        elif hasattr(response, "error"):
            raise Exception(f"Supabase error: {response.error}")
        return None  # Or handle unexpected response structure

    # --- Make all data methods synchronous ---

    def get_tasks(self):
        try:
            # Remove await, use sync execute()
            response = self.supabase.table("tasks").select("*").execute()
            return self._handle_response(response)
        except Exception as e:
            print(f"Error in get_tasks: {e}")
            return []

    def get_rewards(self):
        try:
            response = self.supabase.table("rewards").select("*").execute()
            return self._handle_response(response)
        except Exception as e:
            print(f"Error in get_rewards: {e}")
            return []

    def add_task(self, task_data):
        try:
            response = self.supabase.table("tasks").insert(task_data).execute()
            self._handle_response(response)  # Or just check for exceptions
        except Exception as e:
            print(f"Error in add_task: {e}")
            raise  # Re-raise to signal failure

    def add_reward(self, reward_data):
        try:
            response = self.supabase.table("rewards").insert(reward_data).execute()
            self._handle_response(response)
        except Exception as e:
            print(f"Error in add_reward: {e}")
            raise

    # user_id might not be needed if RLS is based on auth.uid()
    def add_task_history(self, task_history_data):
        try:
            response = (
                self.supabase.table("task_history").insert(task_history_data).execute()
            )
            self._handle_response(response)
        except Exception as e:
            print(f"Error in add_task_history: {e}")
            raise

    # user_id might not be needed if RLS is based on auth.uid()
    def add_reward_history(self, reward_history_data):
        try:
            response = (
                self.supabase.table("reward_history")
                .insert(reward_history_data)
                .execute()
            )
            self._handle_response(response)
        except Exception as e:
            print(f"Error in add_reward_history: {e}")
            raise

    def delete_task(self, task_id):
        try:
            response = self.supabase.table("tasks").delete().eq("id", task_id).execute()
            self._handle_response(response)
        except Exception as e:
            print(f"Error in delete_task: {e}")
            raise

    def delete_reward(self, reward_id):
        try:
            response = (
                self.supabase.table("rewards").delete().eq("id", reward_id).execute()
            )
            self._handle_response(response)
        except Exception as e:
            print(f"Error in delete_reward: {e}")
            raise

    # user_id might not be needed if RLS is based on auth.uid()
    def get_task_history(self, user_id):
        try:
            # If RLS is set up correctly, filtering by user_id might be redundant
            # as the authenticated user's context should handle it.
            # However, keeping it might be necessary depending on your RLS policies.
            response = (
                self.supabase.table("task_history").select("*")
                # .eq("user_id", user_id) # Check if needed with RLS
                .execute()
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching task history: {e}")
            return []

    # user_id might not be needed if RLS is based on auth.uid()
    def get_reward_history(self, user_id):
        try:
            response = (
                self.supabase.table("reward_history").select("*")
                # .eq("user_id", user_id) # Check if needed with RLS
                .execute()
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching reward history: {e}")
            return []
