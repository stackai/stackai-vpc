import os
import pickle
import tempfile
import zipfile

from pymongo import MongoClient


def download_templates(mongo_production_client: MongoClient) -> list:
    """Download all templates from the production database

    Args:
        mongo_production_client (MongoClient): A MongoClient object connected to the production database.

    Returns:
        list: A list of all templates in the production database.
    """

    # Get all templates from the database and store them in a variable
    templates_cursor = mongo_production_client["__models__"]["__templates__"].find()

    # Convert the cursor to a list containing all templates
    templates = list(templates_cursor)

    return templates


def generate_templates_zip_from_template_list(
    templates: list, target_path: str
) -> None:
    """Generate a zip file containing the templates from a list of templates

    Args:
        templates (list): A list of all templates to store in the zip file.
        target_path (str): The path to the zip file to be created.

    """

    with tempfile.TemporaryDirectory() as temp_dir:
        for template in templates:
            with open(f"{temp_dir}/{template['key']}.pickle", "wb") as f:
                pickle.dump(template, f)

        with zipfile.ZipFile(target_path, "w") as zip_ref:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zip_ref.write(os.path.join(root, file), file)


def load_templates_from_zip_file(file_path: str) -> list:
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


def remove_existing_templates(mongodb_client: MongoClient):
    """Remove all templates from the new database

    Args:
        mongodb_client (MongoClient): A MongoClient object connected to the new database.
    """
    print("Removing existing templates...")
    mongodb_client["__models__"]["__templates__"].drop()


def get_mongodb_uris_from_user():
    """Ask the user for the connection strings to the production and local MongoDB databases.

    Returns:
        tuple: A tuple containing the connection string to the production database and the connection string to the local database.
    """
    default_local_mongodb_uri = "mongodb://mongodb:27017/?replicaSet=rs0"

    # Ask the user for the connection strings to the production and local MongoDB databases
    mongodb_production_uri = input(
        "Please provide the connection string to the production MongoDB database: "
    )

    print(
        "Please provide the connection string to the local MongoDB database, leave blank to use the default value:"
    )
    mongodb_local_uri = input(f"Connection String [{default_local_mongodb_uri}]: ")
    if mongodb_local_uri == "":
        mongodb_local_uri = default_local_mongodb_uri

    return mongodb_production_uri, mongodb_local_uri


def get_mongodb_client_from_user(input_prompt: str):
    """Ask the user for the connection string to the MongoDB database.

    Returns:
        str: The connection string to the MongoDB database.
    """
    while True:
        mongodb_uri = input(input_prompt)
        try:
            return MongoClient(mongodb_uri)
        except Exception as e:
            print(f"Invalid connection string, please try again. Error: {e}")


if __name__ == "__main__":
    print("=" * 80)
    print("StackAI MongoDB Initialization Script")
    print("=" * 80)

    while True:
        print(
            "Please, input 1 (or leave blank) if you wish to sync the flow templates from a local zip file (default), input 2 if you wish to sync the flow templates from a remote production database: "
        )

        choice = input("Choice (local zip by default): ")
        if choice == "":
            choice = "1"

        if choice == "1":
            path = input(
                "Please provide the path to the zip file containing the templates (empty for default): "
            )
            if path == "":
                path = "templates.zip"
            templates = load_templates_from_zip_file(path)
            break
        elif choice == "2":
            mongo_production_client = get_mongodb_client_from_user(
                "Please provide the connection string to the reference MongoDB database: "
            )
            templates = download_templates(mongo_production_client)
            break
        else:
            print("Invalid choice, please try again.")

    target_mongodb_client = get_mongodb_client_from_user(
        "Please provide the connection string to the target MongoDB database: "
    )

    print(
        f"\n\nA total of {len(templates)} templates will be uploaded to the target database..."
    )

    remove_existing_templates(target_mongodb_client)
    upload_templates_from_list(target_mongodb_client, templates)

    print("*" * 80)
    print("Success! Happy Stacking :)")
    print("*" * 80)
