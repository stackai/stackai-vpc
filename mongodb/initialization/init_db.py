from pymongo import MongoClient
from argparse import ArgumentParser


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


def upload_templates_from_list(mongo_local_client: MongoClient, templates: list):
    """Upload all templates to the new database

    Args:
        mongo_local_client (MongoClient): A MongoClient object connected to the new database.
        templates (list): A list of all templates to upload to the new database.
    """
    # Insert the templates into the database
    mongo_local_client["__models__"]["__templates__"].insert_many(templates)


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


if __name__ == "__main__":
    print("StackAI MongoDB Initialization Script")
    print("===================================")

    mongodb_production_uri, mongodb_local_uri = get_mongodb_uris_from_user()

    print("STEP 0: Creating MongoDB clients...")
    mongo_production_client = MongoClient(mongodb_production_uri)
    mongo_local_client = MongoClient(mongodb_local_uri)

    print("STEP 1: Syncing flow templates from production to the new database...")
    templates = download_templates(mongo_production_client)
    print(
        f"\t - Found {len(templates)} templates in the production database. Uploading to the new database..."
    )
    upload_templates_from_list(mongo_local_client, templates)

    print("STEP 1: Success!")
