import os
import pathlib
import pickle
import tempfile
import zipfile

import toml
from dotenv import load_dotenv
from pymongo import MongoClient

########################################################
# MONGODB TEMPLATES
########################################################


def remove_existing_templates(mongodb_client: MongoClient):
    """Remove all templates from the new database

    Args:
        mongodb_client (MongoClient): A MongoClient object connected to the new database.
    """
    print("\tRemoving existing templates...")
    mongodb_client["__models__"]["__templates__"].drop()


def load_templates_from_zip_file(file_path: pathlib.Path) -> list:
    """Load templates from a zip file

    Args:
        file_path (str): The path to the zip file containing the templates.

    Returns:
        list: A list of all templates in the zip file.
    """

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        # extract the zip file to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_ref.extractall(temp_dir)

            # load the templates from the temporary directory
            templates = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    with open(os.path.join(root, file), "rb") as f:
                        templates.append(pickle.load(f))

    return templates


def upload_templates_from_list(mongo_local_client: MongoClient, templates: list):
    """Upload all templates to the new database

    Args:
        mongo_local_client (MongoClient): A MongoClient object connected to the new database.
        templates (list): A list of all templates to upload to the new database.
    """
    print("\tUploading templates...")
    mongo_local_client["__models__"]["__templates__"].insert_many(templates)


def update_templates(project_root_path: pathlib.Path, templates_zip_path: pathlib.Path):
    # load the .env file from the mongodb folder to get the connection string
    dotenv_path = project_root_path / "mongodb" / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    mongodb_connection_string = f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@localhost:27017"

    # connect to the new database
    mongodb_client = MongoClient(mongodb_connection_string)

    # Load templates from zip file
    templates = load_templates_from_zip_file(templates_zip_path)

    # remove existing templates
    remove_existing_templates(mongodb_client)

    # upload templates
    upload_templates_from_list(mongodb_client, templates)


########################################################
# UPDATE LLM CONFIG
########################################################


def load_llm_local_config(root_path: pathlib.Path):
    llm_local_config_path = root_path / "stackend" / "llm_local_config.toml"
    with open(llm_local_config_path, "r") as f:
        return toml.load(f)


def update_llm_local_config(root_path: pathlib.Path):
    llm_local_config_path = root_path / "stackend" / "llm_local_config.toml"

    toml_file = toml.load(llm_local_config_path)

    for x, v in toml_file["llms"]["providers"]["Local"].items():
        # rename the model_name to name and add has_function_calling if not present
        if "name" in v and x != "default":
            v["model_name"] = v["name"]
            del v["name"]
            if "has_function_calling" not in v:
                v["has_function_calling"] = False

        # in [llms.providers.Local.default] change model_name to model_id
        if x == "default" and "model_name" in v:
            v["model_id"] = v["model_name"]
            del v["model_name"]

    with open(llm_local_config_path, "w") as f:
        toml.dump(toml_file, f)


def copy_new_stackweb_files(stackai_root_path: pathlib.Path):
    new_files_path = pathlib.Path(__file__).parent / "stackweb"
    os.chdir(stackai_root_path)
    os.system(f"cp -rf {new_files_path}/* stackweb/")


def add_new_env_vars(stackai_root_path: pathlib.Path):
    env_file_path = stackai_root_path / "stackweb" / ".env"

    env_var = '\nNEXT_PUBLIC_SHAREPOINT_CLIENT_ID="<your-sharepoint-client-id>"\n'

    # Append to file using with statement (safer file handling)
    with open(env_file_path, "a") as f:
        f.write(env_var)


############################################################
# DOCKER
############################################################


def build_frontend_container(stackai_root_path: pathlib.Path):
    os.chdir(stackai_root_path)
    os.system("docker compose build stackweb")


def pull_latest_docker_images(stackai_root_path: pathlib.Path):
    os.chdir(stackai_root_path)
    os.system("docker compose pull stackend celery_worker")


def run_database_migrations(stackai_root_path: pathlib.Path):
    os.chdir(stackai_root_path)
    os.system("docker compose up -d stackend")
    os.system(
        'docker compose exec stackend bash -c "cd infra/migrations/postgres && alembic upgrade head"'
    )


def start_all_services(stackai_root_path: pathlib.Path):
    os.chdir(stackai_root_path)
    os.system("docker compose up -d")


def stop_stack_services(stackai_root_path: pathlib.Path):
    os.chdir(stackai_root_path)
    os.system("docker compose stop stackweb stackend celery_worker")


########################################################
# MISC.
########################################################


def get_stackai_root_path_from_user() -> pathlib.Path:
    """Gets the absolute path to the root folder of the on premise installation from the user.

    Returns:
        pathlib.Path: The absolute path to the root folder of the on premise installation.
    """
    while True:
        print(
            "Please input the absolute path to the root folder of your on premise installation (the one containing the stackend/ stackweb/ etc. folders)."
        )
        print("Press CTRL+C to exit.")
        path = input("Path: ")

        try:
            validated_path = pathlib.Path(path)
            # get the list of children directories
            children_directories = [
                child for child in validated_path.iterdir() if child.is_dir()
            ]

            if not any(
                child.name == "stackweb" for child in children_directories
            ) or not any(child.name == "stackend" for child in children_directories):
                print(
                    "The provided path does not seem to contain a valid on premise installation. Please try again..."
                )
                continue
        except:
            print(f"The provided path ({path}) is not valid. Please try again...")
            continue

        return validated_path


if __name__ == "__main__":
    print("\n\n\n")
    print(" === STACK AI ON PREMISE UPDATE SCRIPT === ")
    stackai_root_path = get_stackai_root_path_from_user()

    print(f"The update script will be executed against: {stackai_root_path}\n")

    print("Stopping stack services...")
    stop_stack_services(stackai_root_path)

    print(
        "STEP 1: Copy the new dockerfile and docker-compose yml files in the frontend folder..."
    )
    copy_new_stackweb_files(stackai_root_path)

    print(
        "STEP 2: Adding the NEXT_PUBLIC_SHAREPOINT_CLIENT_ID environment variable to the stackweb/.env file..."
    )
    add_new_env_vars(stackai_root_path)

    print("STEP 3: Building the frontend container...")
    build_frontend_container(stackai_root_path)

    print("STEP 3: Pulling the latest backend docker images...")
    os.chdir(stackai_root_path)
    os.system("docker compose pull stackend celery_worker")

    print("STEP 3: Updating llm_local_config.toml...")
    update_llm_local_config(stackai_root_path)

    print("STEP 4: Running database migrations...")
    run_database_migrations(stackai_root_path)

    print("FINAL STEP: Updating mongodb templates...")
    templates_zip_path = (
        pathlib.Path(__file__).parent / "scripts" / "mongodb" / "templates.zip"
    )
    # make sure the templates zip file exists
    if not templates_zip_path.exists():
        print(
            f"The templates zip file ({templates_zip_path}) does not exist. Please make sure it exists and try again..."
        )
        exit(1)

    update_templates(stackai_root_path, templates_zip_path)
    print("UPDATES COMPLETED SUCCESSFULLY!")
    print("Starting all services...")
    print("Happy Stacking! :)")

    start_all_services(stackai_root_path)
