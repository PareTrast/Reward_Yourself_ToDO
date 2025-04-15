# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\user_manager.py
import flet as ft
import os
import sys
import traceback  # Import traceback


# --- Import ClientOptions ---
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions  # <-- Import this

# --- End Import ---
from user_storage import FileSystemUserStorage
from dotenv import load_dotenv
import json
import requests
from requests.exceptions import RequestException, HTTPError
import config_loader

load_dotenv()

print("Running in web environment:", "pyodide" in sys.modules)


class UserManager:
    def __init__(self, page: ft.Page, users_dir="users"):
        self.page = page
        self.users_dir = users_dir
        self.user_storage = self.get_user_storage()
        self.supabase_url = config_loader.get_supabase_url()
        self.supabase_anon_key = config_loader.get_supabase_anon_key()
        self.supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.admin_supabase: Client = None
        self.public_supabase: Client = None

        print(f"UserManager - URL Loaded: {self.supabase_url is not None}")
        print(f"UserManager - Anon Key Loaded: {self.supabase_anon_key is not None}")
        print(
            f"UserManager - Service Key Loaded: {self.supabase_service_role_key is not None}"
        )
        print(f"UserManager - Running in web environment: {self.page.web}")
        if config_loader.CONFIG_ERROR:
            print(
                f"UserManager - Warning: Configuration error detected: {config_loader.CONFIG_ERROR}"
            )
        # --- Initialize admin client on startup if possible ---
        self.get_admin_supabase_client()  # Try to initialize admin client here
        # --- End modification ---

    # ... (get_user_storage, register_user, verify_user remain the same) ...
    def get_user_storage(self):
        return FileSystemUserStorage(self.users_dir)

    def register_user(self, username, password):
        """Registers a new user using Supabase REST API."""
        if not self.supabase_url or not self.supabase_anon_key:
            print("Error: Supabase URL or Anon Key not configured for registration.")
            return None, None, None

        signup_url = f"{self.supabase_url}/auth/v1/signup"
        headers = {
            "apikey": self.supabase_anon_key,
            "Content-Type": "application/json",
        }
        email = f"{username}@placeholder.com"
        payload = {
            "email": email,
            "password": password,
            "options": {"data": {"username": username, "user_medal_count": 0}},
        }
        try:
            response = requests.post(
                signup_url, headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()
            data = response.json()
            print(f"Register response: {data}")
            user_info = data.get("user", {})
            access_token = data.get("access_token")
            user_id = user_info.get("id")
            refresh_token = data.get("refresh_token")
            return access_token, user_id, refresh_token
        except HTTPError as e:
            print(
                f"Error during registration (HTTP {e.response.status_code}): {e.response.text}"
            )
            if (
                e.response
                and e.response.status_code == 400
                and "User already registered" in e.response.text
            ):
                print("Registration failed: User already exists.")
            elif e.response and e.response.status_code == 422:
                print(f"Registration failed (Validation Error 422): {e.response.text}")
            else:
                print(
                    f"Registration failed (HTTP {e.response.status_code if e.response else 'N/A'})."
                )
            return None, None, None
        except requests.exceptions.Timeout:
            print(f"Timeout Error during registration: {signup_url}")
            return None, None, None
        except RequestException as e:
            print(f"Network error during registration: {e}")
            return None, None, None
        except Exception as e:
            print(f"Unexpected error during registration: {e}")
            return None, None, None

    def verify_user(self, username, password):
        """Verifies a user's credentials using Supabase REST API token endpoint."""
        print("--- verify_user called ---")
        if not self.supabase_url or not self.supabase_anon_key:
            print("Error: Supabase URL or Anon Key not configured for verification.")
            return None, None, None

        token_url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
        headers = {"apikey": self.supabase_anon_key, "Content-Type": "application/json"}
        email = f"{username}@placeholder.com"
        payload = {"email": email, "password": password}
        print(f"Login URL: {token_url}")
        # print(f"Login Headers: {headers}") # Avoid logging keys
        # print(f"Login Payload: {payload}") # Avoid logging passwords
        try:
            response = requests.post(
                token_url, headers=headers, json=payload, timeout=15
            )
            print(f"Login Raw Response Status: {response.status_code}")
            # print(f"Login Raw Response Body: {response.text}") # Avoid logging tokens
            response.raise_for_status()
            data = response.json()
            # print(f"Login Parsed Response Data: {data}") # Avoid logging tokens
            access_token = data.get("access_token")
            user_info = data.get("user", {})
            user_id = user_info.get("id")
            refresh_token = data.get("refresh_token")
            print(f"Extracted access_token: {access_token is not None}")
            print(f"Extracted user_id: {user_id}")
            print(f"Extracted refresh_token: {refresh_token is not None}")
            return access_token, user_id, refresh_token
        except HTTPError as e:
            if e.response.status_code == 400:
                error_detail = "Invalid credentials or user not found"
                try:
                    error_json = e.response.json()
                    if "Email not confirmed" in error_json.get("error_description", ""):
                        error_detail = "Email not confirmed"
                except json.JSONDecodeError:
                    pass
                print(f"Login failed: {error_detail} (HTTP 400).")
            else:
                print(
                    f"Error during login (HTTP {e.response.status_code}): {e.response.text}"
                )
            return None, None, None
        except requests.exceptions.Timeout:
            print(f"Timeout Error during login: {token_url}")
            return None, None, None
        except RequestException as e:
            print(f"Network error during login: {e}")
            return None, None, None
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            return None, None, None

    def get_supabase_client(self) -> Client | None:
        """Returns a synchronous Supabase client using the Anon Key."""
        if not self.supabase_url or not self.supabase_anon_key:
            print(
                "Error: Cannot create public Supabase client. URL or Anon Key missing."
            )
            return None
        if self.public_supabase is None:
            try:
                # --- Use ClientOptions class ---
                # Public client usually operates on the 'public' schema (default)
                client_options = ClientOptions(auto_refresh_token=True, schema="public")
                self.public_supabase = create_client(
                    self.supabase_url,
                    self.supabase_anon_key,
                    options=client_options,  # Pass the ClientOptions instance
                )
                # --- End modification ---
                print("Public synchronous Supabase client created (schema: public).")
            except Exception as e:
                # Log the specific error during client creation
                print(f"Error creating public Supabase client: {e}")
                traceback.print_exc()  # Print full traceback for debugging
                return None
        return self.public_supabase

    # --- Modified get_admin_supabase_client ---
    def get_admin_supabase_client(self) -> Client | None:
        """Returns a synchronous Supabase client with service role key, targeting the 'auth' schema."""
        if not self.supabase_service_role_key:
            print(
                "Warning: SUPABASE_SERVICE_ROLE_KEY not set. Cannot create admin client."
            )
            return None
        if not self.supabase_url:
            print("Error: Cannot create admin Supabase client. URL missing.")
            return None
        if self.admin_supabase is None:
            try:
                # --- Specify the 'auth' schema for the admin client ---
                client_options = ClientOptions(schema="auth")  # Set schema here
                self.admin_supabase = create_client(
                    self.supabase_url,
                    self.supabase_service_role_key,
                    options=client_options,  # Pass the options
                )
                # --- End modification ---
                print(
                    "Admin synchronous Supabase client created (schema: auth)."
                )  # Update log
            except Exception as e:
                print(f"Error creating admin Supabase client: {e}")
                traceback.print_exc()  # Print full traceback for debugging
                return None
        return self.admin_supabase

    # --- End modification ---

    # --- Method to fetch metadata (uses admin client) ---
    def get_user_metadata_admin(self, user_id: str) -> dict | None:
        """Fetches user metadata directly from auth.users using the admin client."""
        print(f"--- get_user_metadata_admin called for user_id: {user_id} ---")
        admin_client = self.get_admin_supabase_client()
        if not admin_client:
            print("Error: Admin client not available to fetch metadata.")
            return None

        try:
            # Use the admin client (now configured for 'auth' schema) to query the 'users' table
            print(f"Querying 'users' table (in auth schema) for id: {user_id}")
            response = (
                admin_client.from_("users")  # Should now correctly target auth.users
                .select("raw_user_meta_data")  # Correct column for direct table query
                .eq("id", user_id)
                .single()  # Expect exactly one row
                .execute()
            )
            print(f"Admin query response data: {response.data}")

            # .single() should return a dict directly in response.data if found
            if response.data:
                # The metadata is usually in the 'raw_user_meta_data' field
                metadata = response.data.get("raw_user_meta_data")
                if isinstance(metadata, dict):
                    print(f"Successfully fetched metadata via admin: {metadata}")
                    return metadata
                # Handle case where raw_user_meta_data might be null in the DB
                elif metadata is None:
                    print(
                        f"User {user_id} found, but 'raw_user_meta_data' is null in the database."
                    )
                    return {}  # Return an empty dict if metadata is explicitly null
                else:
                    # This case is less likely with .single() but good to have
                    print(
                        f"Warning: 'raw_user_meta_data' field is not a dictionary or is missing: {metadata}"
                    )
                    return None
            else:
                # This case might be reached if .single() fails unexpectedly without raising an error
                print(
                    f"No user found or unexpected response structure for ID {user_id} via admin query."
                )
                return None

        except Exception as e:
            # .single() will raise an exception if 0 or >1 rows are found
            print(f"Error querying auth.users via admin client (using .single()): {e}")
            traceback.print_exc()  # Print full traceback for debugging
            return None

    # --- End Method ---
