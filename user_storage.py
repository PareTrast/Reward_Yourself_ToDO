import os
import json
from supabase import create_async_client, AsyncClient  # Import create_async_client
from gotrue.errors import AuthApiError
from dotenv import load_dotenv

load_dotenv()


class UserStorage:
    async def register_user(self, username, password, admin_supabase):
        raise NotImplementedError

    async def verify_user(
        self, username, password, public_supabase
    ):  # Add public_supabase parameter
        raise NotImplementedError

    def get_access_token(self, username):
        raise NotImplementedError

    def get_refresh_token(self, username):
        raise NotImplementedError


class FileSystemUserStorage(UserStorage):
    def __init__(self, users_dir="users"):
        self.users_dir = users_dir
        os.makedirs(self.users_dir, exist_ok=True)

    async def register_user(self, username, password, admin_supabase):
        try:
            response = await admin_supabase.auth.sign_up(
                {
                    "email": f"{username}@placeholder.com",
                    "password": password,
                    "options": {"data": {"username": username}},
                }
            )
            if hasattr(response, "error") and response.error:
                print(f"Error registering user: {response.error}")
                return False, None, None, None
            else:
                user_id = response.user.id
                try:
                    update_response = await admin_supabase.auth.admin.update_user_by_id(
                        user_id, {"user_metadata": {"role": "user"}}
                    )
                    if hasattr(update_response, "error") and update_response.error:
                        print(f"Error updating user metadata: {update_response.error}")
                        return False, None, None, None
                except Exception as e:
                    print(f"Error updating user metadata: {e}")
                    return False, None, None, None

                sign_in_response = await admin_supabase.auth.sign_in_with_password(
                    {"email": f"{username}@placeholder.com", "password": password}
                )
                if sign_in_response.session:
                    access_token = sign_in_response.session.access_token
                    refresh_token = sign_in_response.session.refresh_token
                    user_id = sign_in_response.session.user.id
                    print(
                        f"register_user - access_token: {access_token}, type: {type(access_token)}"
                    )
                    print(
                        f"register_user - refresh_token: {refresh_token}, type: {type(refresh_token)}"
                    )
                    if not isinstance(refresh_token, str):
                        print("register_user - refresh_token is not a string!")
                    self.store_tokens(username, access_token, refresh_token)
                    return True, access_token, refresh_token, user_id
                else:
                    print(f"Error signing in after registration: {sign_in_response}")
                    return False, None, None, None
        except AuthApiError as e:
            print(f"Error registering user: {e}")
            return False, None, None, None

    async def verify_user(
        self, username, password, public_supabase
    ):  # Add public_supabase parameter
        response = await public_supabase.auth.sign_in_with_password(
            {"email": f"{username}@placeholder.com", "password": password}
        )
        print(f"verify_user - response: {response}")
        if response.session:
            access_token = response.session.access_token
            refresh_token = response.session.refresh_token
            user_id = response.session.user.id
            print(
                f"verify_user - access_token: {access_token}, type: {type(access_token)}"
            )
            print(
                f"verify_user - refresh_token: {refresh_token}, type: {type(refresh_token)}"
            )
            print(f"verify_user - user_id: {user_id}")
            if not isinstance(refresh_token, str):
                print("verify_user - refresh_token is not a string!")
            self.store_tokens(username, access_token, refresh_token)
            return access_token, refresh_token, user_id
        else:
            print("verify_user - sign in failed")
            return None, None, None

    def get_access_token(self, username):
        tokens = self.get_tokens(username)
        if tokens:
            return tokens["access_token"]
        return None

    def get_refresh_token(self, username):
        tokens = self.get_tokens(username)
        if tokens:
            return tokens["refresh_token"]
        return None

    def get_tokens(self, username):
        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"get_tokens - Error decoding JSON from file: {e}")
                return None
            except Exception as e:
                print(f"get_tokens - Error loading tokens: {e}")
                return None
        return None

    def store_tokens(self, username, access_token, refresh_token):
        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        print(f"store_tokens - token_file: {token_file}")
        print(f"store_tokens - username: {username}")
        print(f"store_tokens - access_token: {access_token}")
        print(f"store_tokens - refresh_token: {refresh_token}")
        try:
            with open(token_file, "w") as f:
                json.dump(
                    {"access_token": access_token, "refresh_token": refresh_token}, f
                )
        except Exception as e:
            print(f"store_tokens - Error storing tokens: {e}")

    def remove_access_token(self, username):
        token_file = os.path.join(self.users_dir, f"{username}.tokens")
        print(f"remove_access_token - token_file: {token_file}")
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
            except Exception as e:
                print(f"remove_access_token - Error removing tokens: {e}")
