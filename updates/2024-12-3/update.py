import zipfile
from pymongo import MongoClient
from dotenv import load_dotenv
import pathlib
import os
import tempfile
import pickle
import toml

########################################################
# MONGODB TEMPLATES
########################################################

def remove_existing_templates(mongodb_client: MongoClient):
    """Remove all templates from the new database

    Args:
        mongodb_client (MongoClient): A MongoClient object connected to the new database.
    """
    print("Removing existing templates...")
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
    print("Uploading templates...")
    mongo_local_client["__models__"]["__templates__"].insert_many(templates)


def update_templates(project_root_path: pathlib.Path, templates_zip_path: pathlib.Path):
    # load the .env file from the mongodb folder to get the connection string
    dotenv_path = project_root_path /'mongodb'/'.env'
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

    # rename the model_name to name and add has_function_calling if not present
    for x, v in toml_file["llms"]["providers"]["Local"].items():
        if "name" in v:
            v["model_name"] = v["name"]
            del v["name"]
            if "has_function_calling" not in v:
                v["has_function_calling"] = False

    # in [llms.providers.Local.default] change model_name to model_id
    toml_file["llms"]["providers"]["Local"]["default"]["model_id"] = toml_file["llms"]["providers"]["Local"]["default"]["model_name"]
    del toml_file["llms"]["providers"]["Local"]["default"]["model_name"]

    with open(llm_local_config_path, "w") as f:
        toml.dump(toml_file, f)


########################################################
# MISC.
########################################################

def get_stackai_root_path_from_user() -> pathlib.Path:
    """Gets the absolute path to the root folder of the on premise installation from the user.

    Returns:
        pathlib.Path: The absolute path to the root folder of the on premise installation.
    """
    while True:
        print("Please input the absolute path to the root folder of your on premise installation (the one containing the stackend/ stackweb/ etc. folders).")
        print("Press CTRL+C to exit.")
        path = input("Path: ")

        try:
            validated_path = pathlib.Path(path)
            # get the list of children directories
            children_directories = [child for child in validated_path.iterdir() if child.is_dir()]

            if not any(child.name == "stackweb" for child in children_directories) or not any(child.name == "stackend" for child in children_directories):
                print("The provided path does not seem to contain a valid on premise installation. Please try again...")
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

    print("STEP 1: Updating llm_local_config.toml...")
    update_llm_local_config(stackai_root_path)

    print("FINAL STEP: Updating mongodb templates...")
    templates_zip_path = pathlib.Path(__file__).parent / 'scripts' / 'mongodb' / 'templates.zip'
    # make sure the templates zip file exists
    if not templates_zip_path.exists():
        print(f"The templates zip file ({templates_zip_path}) does not exist. Please make sure it exists and try again...")
        exit(1)

    update_templates(stackai_root_path, templates_zip_path)
    print("UPDATES COMPLETED SUCCESSFULLY!")
    print("Happy Stacking! :)")