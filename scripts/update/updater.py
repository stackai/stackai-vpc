import os
import sys
import shutil
import zipfile
import tempfile
import requests # type: ignore
from pathlib import Path

# Define the repository and branch
REPO_OWNER = "stackai"
REPO_NAME = "stackai-onprem"
BRANCH = "main"
ZIP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"

# Known service directories that might contain .env files to preserve
# These paths are relative to the project root
SERVICE_DIRS_WITH_ENV = [
    Path("caddy"), Path("mongodb"), Path("stackend"), Path("stackrepl"),
    Path("stackweb"), Path("supabase"), Path("unstructured"), Path("weaviate")
]

# Patterns to exclude during synchronization from the extracted ZIP to the project root.
# These are relative to the root of the extracted ZIP contents.
# - .git/ is excluded to preserve local git history.
# - .env files at the root of a service dir are handled by specific logic to preserve user versions.
# - Common cache/temporary/dependency directories.
EXCLUDE_PATTERNS = [
    ".git",                   # Git history and configuration
    ".github",                # GitHub specific files, not needed for deployment
    ".idea",                  # IDE specific files
    ".vscode",                # VSCode specific files
    "__pycache__",            # Python bytecode cache
    "*.pyc", "*.pyo",         # Python compiled files
    ".DS_Store",              # macOS specific
    "node_modules",           # Node.js dependencies
    ".venv",                  # Python virtual environments (if accidentally included)
    "*.log",                  # Log files
    "build", "dist",          # Common build output directories
    "*.egg-info",             # Python packaging metadata
    "updates",                # The updates directory itself, if it exists at root
    "*.tmp",                  # Temporary files
    "*.bak",                  # Backup files
    "*.swp"                   # Swap files
]

def is_project_root(path: Path) -> bool:
    """Check if the given path looks like the project root."""
    return (
        (path / "docker-compose.yml").is_file() and
        (path / "scripts").is_dir() and
        (path / "stackweb").is_dir() # Add another characteristic check
    )

def find_project_root_auto() -> Path | None:
    """Try to automatically find the project root directory."""
    # The script itself is in scripts/update/updater.py
    # So, current_script_path is .../scripts/update/updater.py
    # Parent of updater.py is .../scripts/update/
    # Parent of that is .../scripts/
    # Parent of that should be the project root.
    current_script_path = Path(__file__).resolve()
    potential_root = current_script_path.parent.parent.parent
    if is_project_root(potential_root):
        return potential_root
    
    # Fallback: Check current working directory and its parents
    # This is useful if the script is called from an unexpected location
    # but the CWD is somewhere within the project.
    cwd = Path.cwd().resolve()
    current_path = cwd
    while current_path != current_path.parent: # Stop at filesystem root
        if is_project_root(current_path):
            return current_path
        current_path = current_path.parent
    if is_project_root(current_path): # Check root itself
            return current_path
    return None

def get_project_root_interactively() -> Path | None:
    """Prompt the user for the project root path, max 3 attempts."""
    attempts = 3
    while attempts > 0:
        print(f"Could not automatically determine the project root directory (attempt {4 - attempts}/3).")
        user_path_str = input("Please enter the full path to your 'stackai-onprem' directory: ").strip()
        if not user_path_str:
            print("No path entered.")
            attempts -= 1
            continue
        
        user_path = Path(user_path_str).resolve()
        if is_project_root(user_path):
            return user_path
        else:
            print(f"The path '{user_path_str}' does not appear to be a valid project root.")
            print("A valid root should contain 'docker-compose.yml', 'scripts/', and 'stackweb/' directories/files.")
            attempts -= 1
    
    print("Failed to obtain a valid project root path after 3 attempts. Aborting.")
    return None

def is_excluded(path: Path, project_root_in_zip: Path) -> bool:
    """Check if a path (relative to extracted zip root) should be excluded."""
    try:
        relative_path_obj = path.relative_to(project_root_in_zip)
    except ValueError:
        return False # Not under the zip root, so not excluded by these patterns

    # Convert to string for easier matching, especially for directory parts
    relative_path_str = str(relative_path_obj)

    for pattern in EXCLUDE_PATTERNS:
        # Direct match for files or top-level directories without trailing slash
        if relative_path_obj.name == pattern:
            return True
        # Glob-like matching for files (e.g., *.log)
        if "*" in pattern and relative_path_obj.match(pattern):
            return True
        # Directory name check (e.g., if "node_modules" is a part of the path)
        if pattern in relative_path_obj.parts:
            return True
        # Starts with check for directories (e.g., exclude all under .git/)
        if relative_path_str.startswith(pattern + "/") or relative_path_str == pattern:
            return True
            
    return False

def sync_files(source_dir: Path, dest_dir: Path):
    """Synchronize files from source_dir to dest_dir, respecting exclusions."""
    print(f"Starting synchronization from {source_dir} to {dest_dir}")
    # GitHub ZIPs usually extract to a directory like reponame-branchname
    # We need to find this directory first.
    extracted_content_dirs = [d for d in source_dir.iterdir() if d.is_dir() and REPO_NAME in d.name]
    if not extracted_content_dirs:
        print(f"Error: Could not find the main content directory (e.g., '{REPO_NAME}-{BRANCH}') in {source_dir}.")
        print(f"Contents of {source_dir}: {[item.name for item in source_dir.iterdir()]}")
        return False
    actual_source_root = extracted_content_dirs[0]
    if len(extracted_content_dirs) > 1:
        print(f"Warning: Multiple potential content directories found in {source_dir}. Using {actual_source_root.name}")

    print(f"Identified source content root as: {actual_source_root}")

    copied_count = 0
    skipped_count = 0

    for item_in_source in actual_source_root.rglob("*"):
        if not item_in_source.exists(): # Item might have been removed if its parent dir was excluded and deleted
            continue
        
        relative_path_to_zip_content_root = item_in_source.relative_to(actual_source_root)
        dest_path = dest_dir / relative_path_to_zip_content_root

        if is_excluded(item_in_source, actual_source_root):
            # print(f"  Skipping (excluded pattern): {relative_path_to_zip_content_root}")
            skipped_count += 1
            if item_in_source.is_dir() and dest_path.exists() and False: # Consider if we need to rm for excluded dirs
                 # shutil.rmtree(dest_path) # Risky if dest_path is not what we expect.
                 pass
            continue

        is_service_env = False
        if item_in_source.name == ".env":
            # Check if this .env file is directly within one of the known service directories *in the source structure*
            # e.g., .../stackai-onprem-main/stackweb/.env
            if item_in_source.parent.name in [s.name for s in SERVICE_DIRS_WITH_ENV] and \
               item_in_source.parent.parent == actual_source_root : # ensure it's a top-level service dir
                is_service_env = True
        
        if is_service_env and dest_path.exists():
            # print(f"  Skipping (preserving user's .env): {dest_path}")
            skipped_count += 1
            continue
        
        if item_in_source.name.endswith(".env.example"):
            corresponding_env = dest_path.with_name(".env")
            if corresponding_env.exists():
                # print(f"  Skipping .env.example (user has .env): {relative_path_to_zip_content_root}")
                skipped_count +=1
                continue

        try:
            if item_in_source.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item_in_source, dest_path)
                copied_count +=1
        except Exception as e:
            print(f"  Error copying {item_in_source} to {dest_path}: {e}")
            skipped_count +=1

    print(f"Synchronization: {copied_count} items copied, {skipped_count} items skipped/preserved.")
    return True

def main():
    project_root = find_project_root_auto()
    if not project_root:
        project_root = get_project_root_interactively()
    
    if not project_root:
        sys.exit(1) # Failed to get project root

    # Change CWD to project root for consistency if needed by other parts, though Path objects are absolute
    # os.chdir(project_root) 
    print(f"Updating project at: {project_root}")

    with tempfile.TemporaryDirectory(prefix="stackai-update-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        zip_path = temp_dir / "repo.zip"

        print(f"Downloading {ZIP_URL} to {zip_path}...")
        try:
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            response.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("Download complete.")
        except requests.RequestException as e:
            print(f"Error downloading repository: {e}")
            sys.exit(1)

        extract_to_dir = temp_dir / "extracted_repo"
        extract_to_dir.mkdir()

        print(f"Extracting {zip_path} to {extract_to_dir}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to_dir)
            print("Extraction complete.")
        except zipfile.BadZipFile as e:
            print(f"Error extracting ZIP file: {e}")
            sys.exit(1)

        if not sync_files(extract_to_dir, project_root):
            print("File synchronization failed. See messages above.")
            sys.exit(1)

    print("Update process finished successfully.")
    print("Please review any .env.example files and update your .env configurations as needed.")
    print("If the update included changes to dependencies (e.g., Python, Node.js), install them.")
    print("Check if any database migrations are required (e.g., 'make run-postgres-migrations').")

if __name__ == "__main__":
    # project_root_arg will no longer be passed from shell script
    main() 