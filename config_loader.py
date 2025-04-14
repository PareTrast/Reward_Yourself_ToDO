import json
import os

CONFIG_FILE = "config.json"
SUPABASE_URL = None
SUPABASE_ANON_KEY = None
CONFIG_ERROR = None

# Determine the base path (works for both script execution and frozen executables/APKs)
# Flet apps often run from a temporary directory when packaged, so finding config.json
# relative to the script location might be needed.
try:
    # If running as a script
    base_path = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # If frozen (e.g., PyInstaller, maybe Flet build)
    import sys

    base_path = os.path.dirname(sys.executable)  # Or sys._MEIPASS for PyInstaller

config_path = os.path.join(base_path, CONFIG_FILE)
print(f"Attempting to load configuration from: {config_path}")

try:
    with open(config_path, "r") as f:
        config_data = json.load(f)

    SUPABASE_URL = config_data.get("SUPABASE_URL")
    # Prioritize SUPABASE_ANON_KEY, but fall back to SUPABASE_KEY if only that exists
    SUPABASE_ANON_KEY = config_data.get(
        "SUPABASE_ANON_KEY", config_data.get("SUPABASE_KEY")
    )

    if not SUPABASE_URL:
        CONFIG_ERROR = f"SUPABASE_URL not found or empty in {config_path}"
    if not SUPABASE_ANON_KEY:
        CONFIG_ERROR = (
            f"SUPABASE_ANON_KEY (or SUPABASE_KEY) not found or empty in {config_path}"
        )

except FileNotFoundError:
    CONFIG_ERROR = f"Configuration file '{config_path}' not found. Ensure '{CONFIG_FILE}' exists and is included in the build."
except json.JSONDecodeError:
    CONFIG_ERROR = f"Error decoding JSON from '{config_path}'. Please check its format."
except Exception as e:
    CONFIG_ERROR = f"An unexpected error occurred loading configuration: {e}"

# Print error prominently if loading failed
if CONFIG_ERROR:
    print(f"####################################################")
    print(f"### Configuration Error: {CONFIG_ERROR} ###")
    print(f"####################################################")
    # You might want to raise an exception here if the app cannot run without config
    # raise RuntimeError(CONFIG_ERROR)


def get_supabase_url():
    """Returns the loaded Supabase URL."""
    if CONFIG_ERROR:
        print(
            f"Warning: Returning potentially None URL due to config error: {CONFIG_ERROR}"
        )
    return SUPABASE_URL


def get_supabase_anon_key():
    """Returns the loaded Supabase Anon Key."""
    if CONFIG_ERROR:
        print(
            f"Warning: Returning potentially None Anon Key due to config error: {CONFIG_ERROR}"
        )
    return SUPABASE_ANON_KEY


# You can also import the variables directly if preferred:
# from config_loader import SUPABASE_URL, SUPABASE_ANON_KEY, CONFIG_ERROR
