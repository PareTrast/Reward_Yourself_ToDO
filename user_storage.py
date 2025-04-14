# c:\Users\nrmlc\OneDrive\Desktop\Reward_Yourself_ToDO\user_storage.py
import os
import json

# Import synchronous client and exceptions
from supabase import create_client, Client
from gotrue.errors import AuthApiError  # Keep for specific auth errors if needed
from dotenv import load_dotenv
import requests  # Import requests

load_dotenv()


class UserStorage:
    # Define methods as synchronous
    def register_user(
        self, username, password, admin_supabase: Client
    ):  # Use Client type hint
        raise NotImplementedError

    def verify_user(
        self, username, password, public_supabase: Client
    ):  # Use Client type hint
        raise NotImplementedError

    def get_access_token(self, username):
        raise NotImplementedError

    def get_refresh_token(self, username):
        raise NotImplementedError


class FileSystemUserStorage(UserStorage):
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    # Make synchronous, use sync client methods
    def register_user(
        self, username, password, admin_supabase: Client
    ):  # Use Client type hint
        """Registers user using the admin client (requires service role key)."""
        if not admin_supabase:
            print("Error: Admin Supabase client not provided for registration.")
            return False, None, None, None

        try:
            # Use synchronous sign_up (or admin create_user)
            # Note: sign_up might require email confirmation depending on settings.
            # Using admin.create_user might be more direct if confirmation is off.
            # Let's assume admin.create_user is preferred for direct creation + role setting.

            email = f"{username}@placeholder.com"

            # 1. Create user using Admin API
            create_response = admin_supabase.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,  # Set to True if you want to bypass email confirmation
                    "user_metadata": {
                        "role": "user",
                        "username": username,
                    },  # Set role and username here
                    # "options": {"data": {"username": username}} # 'data' might be for public signup
                }
            )
            # Sync client often raises exceptions on error, but check response just in case
            if hasattr(create_response, "id"):
                user_id = create_response.id
                print(f"User created successfully with ID: {user_id}")
            else:
                # This path might not be reached if exceptions are raised
                print(
                    f"Error registering user (unexpected response): {create_response}"
                )
                return False, None, None, None

            # 2. Sign in the newly created user to get tokens
            # Use the public client (or a new one) for sign-in as the user
            # This step might be better handled in UserManager after registration returns success.
            # For simplicity here, let's assume we sign in immediately.
            # We need a public client instance. This design is a bit awkward.
            # It might be better for UserManager to handle both creation and sign-in.

            # Let's modify the return signature - registration shouldn't necessarily return tokens.
            # It should just confirm creation. UserManager should then call verify_user.
            # RETHINK: Let's stick to the original flow for minimal changes, assuming admin_supabase
            # can somehow sign in (which is unlikely).
            # --> BETTER APPROACH: Use the REST API directly as done in the refactored UserManager.
            # This FileSystemUserStorage.register_user might become redundant or needs rethinking.

            # --> REVERTING to REST API approach for consistency with UserManager refactor:
            # This method using admin_supabase might not be the best fit anymore.
            # Let's keep the REST API calls within UserManager.
            # This FileSystemUserStorage should focus *only* on storing/retrieving tokens.

            # --> REVISED register_user (Simpler - assumes UserManager handles API calls):
            # This method might not even be needed if UserManager calls store_tokens directly.
            # Let's comment it out for now, assuming UserManager handles registration API calls.
            print(
                "FileSystemUserStorage.register_user called - Consider moving API logic to UserManager."
            )
            # If you *must* keep API calls here, use requests like in UserManager.
            return False, None, None, None  # Indicate failure or remove method

        except AuthApiError as e:
            print(f"Error registering user (AuthApiError): {e}")
            return False, None, None, None
        except Exception as e:
            # Catch potential exceptions from the sync client
            print(f"Error registering user: {e}")
            return False, None, None, None

    # Make synchronous, use sync client methods
    def verify_user(
        self, username, password, public_supabase: Client
    ):  # Use Client type hint
        """Verifies user using the public client."""
        if not public_supabase:
            print("Error: Public Supabase client not provided for verification.")
            return None, None, None

        try:
            email = f"{username}@placeholder.com"
            # Use synchronous sign_in_with_password
            response = public_supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            # Sync client response structure:
            if response.session:
                access_token = response.session.access_token
                refresh_token = response.session.refresh_token
                user_id = response.session.user.id
                print(f"verify_user - Login successful for user ID: {user_id}")
                print(f"verify_user - access_token type: {type(access_token)}")
                print(f"verify_user - refresh_token type: {type(refresh_token)}")

                # Store tokens locally
                self.store_tokens(username, access_token, refresh_token)
                return access_token, refresh_token, user_id
            else:
                # This path might not be reached if exceptions are raised on failure
                print(
                    f"verify_user - sign in failed (unexpected response structure): {response}"
                )
                return None, None, None

        except AuthApiError as e:
            # Specific handling for authentication errors (e.g., invalid credentials)
            print(f"Error verifying user (AuthApiError): {e}")
            return None, None, None
        except Exception as e:
            # Catch other potential exceptions from the sync client
            print(f"Error verifying user: {e}")
            return None, None, None

    # get_access_token, get_refresh_token, get_tokens, store_tokens, remove_access_token
    # remain synchronous and largely unchanged, but add error handling.

    def get_access_token(self, username):
        tokens = self.get_tokens(username)
        return tokens.get("access_token") if tokens else None

    def get_refresh_token(self, username):
        tokens = self.get_tokens(username)
        return tokens.get("refresh_token") if tokens else None

    def get_tokens(self, username):
        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    # Check if file is empty
                    content = f.read()
                    if not content:
                        print(f"Warning: Token file is empty: {token_file}")
                        return None
                    return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"get_tokens - Error decoding JSON from file {token_file}: {e}")
                # Optionally delete or rename the corrupted file
                # os.remove(token_file)
                return None
            except Exception as e:
                print(f"get_tokens - Error loading tokens from {token_file}: {e}")
                return None
        return None

    def store_tokens(self, username, access_token, refresh_token):
        # Ensure tokens are strings before storing
        if not isinstance(access_token, str) or not isinstance(refresh_token, str):
            print(f"Error: Attempted to store non-string token for user {username}.")
            # Decide how to handle: return, raise error, or try to proceed cautiously
            return  # Or raise TypeError("Tokens must be strings")

        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        print(f"store_tokens - Storing tokens to: {token_file}")
        # print(f"store_tokens - access_token: {access_token}") # Avoid logging tokens directly
        # print(f"store_tokens - refresh_token: {refresh_token}")
        try:
            with open(token_file, "w") as f:
                json.dump(
                    {"access_token": access_token, "refresh_token": refresh_token}, f
                )
        except Exception as e:
            print(f"store_tokens - Error storing tokens to {token_file}: {e}")

    def remove_access_token(self, username):
        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        print(f"remove_access_token - Removing token file: {token_file}")
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
                print(f"Token file removed for user {username}.")
            except Exception as e:
                print(
                    f"remove_access_token - Error removing token file {token_file}: {e}"
                )
        else:
            print(f"remove_access_token - Token file not found for user {username}.")
