def clear_session(page, user_manager, username):
    """
    Clears session variables and tokens.
    """
    # Clear session file or tokens if needed
    if page.web:
        page.client_storage.remove("access_token")
        page.client_storage.remove("refresh_token")
    else:
        user_storage = user_manager.get_user_storage()
        if username:
            user_storage.remove_access_token(username)

    print("Session cleared.")
