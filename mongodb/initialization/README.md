# MongoDB Initialization

This guide provides the steps to initialize MongoDB.

## Prerequisites

- MongoDB should already be running.
- You will need the username and password that you configured while setting up MongoDB.

Packages:

- `python3`
- `pip`
- `virtualenv`

The script will prompt you to enter the connection string for your MongoDB database. This is of the format:

```bash
mongodb://<username>:<password>@<host>:<port>
```

If you are using the default configuration, the connection string will be:

```bash
mongodb://<username>:<password>@localhost:27017
```

## Adding the templates

Open a terminal in **this directory** and run the following command:

```bash
bash initialize_mongodb.sh
```

In case the script errors with `permission denied`, run the following command:

```bash
chmod +x initialize_mongodb.sh
```

Then, run the script again.

By default, the script will use the `templates.zip` file located in this directory to insert the templates into the database. If you want to use a different templates file, you can pass the file path as an argument to the script, for example:

```bash
bash initialize_mongodb.sh /path/to/templates.zip
```

## Notes

- The script will create a virtual environment and install the dependencies.
- The script will deactivate the virtual environment after the initialization.
- The script will remove the virtual environment after the initialization, if it does not, remove the `.venv` directory manually.
