import os
from pathlib import Path
from typing import Dict, Optional

def _get_key_value_from_env_line(line: str) -> tuple[str, str] | None:
    """Helper to extract a key-value pair from a .env file line."""
    stripped_line = line.strip()
    if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
        return None
    key_part, value_part = stripped_line.split("=", 1)
    key = key_part.strip()
    value = value_part.strip()
    if not key:  # Handle cases like "=value" or " =value"
        return None
    return key, value

def get_env_var_by_env_file(var_name: str, env_file: str) -> str | None:
    """Get the value of an environment variable from a given .env file."""
    path = Path(env_file)
    if not path.is_file():
        return None # return None if the file does not exist

    for line in path.read_text().splitlines():
        if line.startswith(f"{var_name}="):
            return line.partition("=")[2].strip()
    return None

def update_env_file_variables(env_file_path: Path, variables_to_update: Dict[str, str]) -> None:
    """Update specific variables in a .env file while preserving other content."""
    if not env_file_path.is_file():
        print(f"Warning: {env_file_path} does not exist. Skipping update.")
        return
    
    # Read all lines
    lines = env_file_path.read_text().splitlines()
    updated_lines = []
    updated_vars = set()
    
    # Process each line
    for line in lines:
        key_value_pair = _get_key_value_from_env_line(line)
        if key_value_pair:
            key, current_value = key_value_pair
            if key in variables_to_update:
                # Update this variable
                updated_lines.append(f"{key}={variables_to_update[key]}")
                updated_vars.add(key)
            else:
                # Keep the original line
                updated_lines.append(line)
        else:
            # Keep comments and empty lines
            updated_lines.append(line)
    
    # Add any variables that weren't found in the file
    for key, value in variables_to_update.items():
        if key not in updated_vars:
            updated_lines.append(f"{key}={value}")
    
    # Write back to file
    with open(env_file_path, "w") as f:
        f.write("\n".join(updated_lines) + "\n")

def get_url_input(prompt: str, current_value: Optional[str] = None) -> str:
    """Get URL input from user with optional default value."""
    if current_value:
        user_input = input(f"{prompt} (current: {current_value}, press Enter to keep): ").strip()
        return user_input if user_input else current_value
    else:
        user_input = input(f"{prompt}: ").strip()
        return user_input if user_input else ""

def main() -> None:
    initial_message = """

StackAI URL Update Script

This script will update the URL configurations in your existing .env files for:
- stackend/.env
- stackweb/.env  
- supabase/.env

You will be prompted for three URLs:
1. APP URL - The main application URL users will access
2. API URL - The backend API URL
3. SUPABASE URL - The Supabase instance URL

If you don't provide a value, the existing value will be kept.
"""

    print(initial_message)

    root_project_path = Path(__file__).absolute().parent.parent.parent

    # Check if .env files exist
    stackend_env_path = root_project_path / "stackend" / ".env"
    stackweb_env_path = root_project_path / "stackweb" / ".env"
    supabase_env_path = root_project_path / "supabase" / ".env"

    missing_files = []
    if not stackend_env_path.is_file():
        missing_files.append("stackend/.env")
    if not stackweb_env_path.is_file():
        missing_files.append("stackweb/.env")
    if not supabase_env_path.is_file():
        missing_files.append("supabase/.env")

    if missing_files:
        print(f"Error: The following .env files are missing: {', '.join(missing_files)}")
        print("Please run the environment variable creation script first.")
        return

    # Get current values
    current_app_url = (
        get_env_var_by_env_file("STACKWEB_URL", "stackend/.env") or
        get_env_var_by_env_file("NEXT_PUBLIC_URL", "stackweb/.env") or
        get_env_var_by_env_file("SITE_URL", "supabase/.env")
    )

    current_api_url = (
        get_env_var_by_env_file("STACKEND_API_URL", "stackend/.env") or
        get_env_var_by_env_file("NEXT_PUBLIC_STACKEND_URL", "stackweb/.env")
    )

    current_supabase_url = (
        get_env_var_by_env_file("NEXT_PUBLIC_SUPABASE_URL", "stackweb/.env") or
        get_env_var_by_env_file("API_EXTERNAL_URL", "supabase/.env")
    )

    print("\n" + "="*60)
    print("URL CONFIGURATION")
    print("="*60)

    # Get user input
    app_url = get_url_input("Enter the APP URL", current_app_url)
    api_url = get_url_input("Enter the API URL", current_api_url)
    supabase_url = get_url_input("Enter the SUPABASE URL", current_supabase_url)

    if not app_url and not api_url and not supabase_url:
        print("No URLs provided. Exiting without changes.")
        return

    print(f"\nUpdating .env files with:")
    if app_url:
        print(f"  APP URL: {app_url}")
    if api_url:
        print(f"  API URL: {api_url}")
    if supabase_url:
        print(f"  SUPABASE URL: {supabase_url}")

    confirm = input("\nContinue with the update? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Update cancelled.")
        return

    # Update stackend/.env
    if app_url or api_url:
        stackend_updates = {}
        if app_url:
            stackend_updates["STACKWEB_URL"] = app_url
        if api_url:
            stackend_updates["STACKEND_API_URL"] = api_url
            stackend_updates["INDEXING_API_URL"] = api_url
        
        print(f"\nUpdating stackend/.env...")
        update_env_file_variables(stackend_env_path, stackend_updates)
        print("✓ stackend/.env updated")

    # Update stackweb/.env
    if app_url or api_url or supabase_url:
        stackweb_updates = {}
        if app_url:
            stackweb_updates["NEXT_PUBLIC_URL"] = app_url
            stackweb_updates["NEXT_PUBLIC_SITE_URL"] = app_url
        if api_url:
            stackweb_updates["NEXT_PUBLIC_INDEX_URL"] = api_url
            stackweb_updates["NEXT_PUBLIC_CHAT_BACKEND_URL"] = api_url
            stackweb_updates["NEXT_PUBLIC_STACKEND_URL"] = api_url
            stackweb_updates["NEXT_PUBLIC_STACKEND_INFERENCE_URL"] = api_url
        if supabase_url:
            stackweb_updates["NEXT_PUBLIC_SUPABASE_URL"] = supabase_url
        
        print(f"\nUpdating stackweb/.env...")
        update_env_file_variables(stackweb_env_path, stackweb_updates)
        print("✓ stackweb/.env updated")

    # Update supabase/.env
    if app_url or supabase_url:
        supabase_updates = {}
        if app_url:
            supabase_updates["SITE_URL"] = app_url
        if supabase_url:
            supabase_updates["API_EXTERNAL_URL"] = supabase_url
            supabase_updates["SUPABASE_PUBLIC_URL"] = supabase_url
        
        print(f"\nUpdating supabase/.env...")
        update_env_file_variables(supabase_env_path, supabase_updates)
        print("✓ supabase/.env updated")

    print(f"\n🎉 URL update completed successfully!")
    print("You can now restart your services to apply the new configuration.")

if __name__ == "__main__":
    main() 