# StackAI Docker Compose Deployment

This repository contains the configuration needed to run StackAI locally using docker compose.

# Requirements

## Hardware

1. At least 64GB of RAM
2. At least 16 CPU cores
3. 1TB of disk space

## Software

- Ubuntu 24.04 LTS
- You will need internet access during the setup process.
- Make` installed.
- Python 3.10 or higher.
- `pip` installed.
- `virtualenv` installed.

Check the steps below for instructions on how to check if you meet this requirement.

- You will need docker and docker compose (compose version v2.26 or higher) installed in your machine. There is a script (see instructions below) that will install them for you if needed.
- You will need access to stackai's container image registry on Azure.
- Depending on how you configure the containers, different ports should be exposed, if you follow the default settings, the following ports need to be exposed:
  - Port 3000: TCP port used for the StackAI frontend HTTP
  - Port 8000: TCP port used for the StackAI backend HTTP
  - Port 8800: TCP port used for the Kong API Gateway HTTP
  - Port 8443: TCP port used for the Kong API Gateway HTTPS
  - Port 9000: TCP port used for the MinIO service.

If you set up the Caddy reverse proxy (See steps below), you may change the ports above for the ports 80 or/and 443.

# File structure

```bash
.
├── caddy
├── mongodb
├── scripts
├── supabase
├── stackend
├── stackrepl
├── stackweb
...
```

Each of the folders in the project contains the configuration for one of the services needed to run StackAI.

After running the environment variables initialization script (see below), each folder will contain a `.env` file with the environment variables needed to run the service. This, along the docker-compose.yml files, are the most important configuration files that may need to be edited.

# Set up process

Follow the instructions in the order they are presented.

## Install make

```bash
sudo apt install make
```

Make sure that make is installed correctly by running:

```bash
make --version
```

## Set up the machine where you will run the deployment

You will need docker and docker compose installed in your machine.

To install them, open a terminal in **the root folder of the project, the same as where this README file is located** and execute the following command, log in again after it finishes:

> :WARNING: The script will log you out from your current session.
> Log in again and verify successful setup running the following command:
> <YOU PROVIDE A COMMAND HERE WITH THE EXPECTED RESULT IF SUCCESSFUL>

```bash
make setup-docker-in-ubuntu
```

## Install python, pip and virtualenv

The commands needed to install python, pip and virtualenv may change depending on your specific distribution.

The following commands should work for most Ubuntu based distributions:

Update the package index:

```bash
sudo apt update
```

Install python3, pip and virtualenv:

```bash
sudo apt install python3-pip python3-venv
```

Ensure that python is installed and working correctly by opening a terminal **in the root folder of the project, the same as where this README file is located** and running the following commands on it:

Start by making sure that the python version is >= 3.8:

```bash
python3 --version
```

Then, make sure that virtualenv is installed and working by running:

```bash
python3 -m venv .venv
```

As a result, you should see a new folder named `.venv` in your current directory.

Then, make sure that you can source the virtual environment by running:

```bash
source .venv/bin/activate
```

Last, make sure that pip is working correctly in the virtual environment by running:

```bash
python3 -m pip install pymongo
```

And then:

```bash
python3 -c "import pymongo; print('pymongo imported successfully')"
```

You can remove the virtual environment by running:

```bash
deactivate
rm -rf .venv
```

## Log in to StackAI's Container Registry

You will need to log in to StackAI's container registry on Azure to pull the images we provided you with.

```bash
docker login -u <the_username_we_provided_you_with> -p <the_password_we_provided_you_with> stackai.azurecr.io
```

## Initialize environment variables

Each of the services has a series of environment variables that need to be configured in order to run it. In this step of the set up process, we will create the `.env` files for all the services. After the script finishes, you should be able to go to find the following files in each service's folder:

```bash
supabase/.env
weaviate/.env
unstructured/.env
stackend/.env
stackrepl/.env
stackweb/.env
...
```

The script will initialize the environment variables with random secrets and a valid default configuration.
It is encouraged that you manually review the generated values after the script finishes and make any adjustments needed, specially to the networking related configuration.

### Istructions

a) Read the section above.

b) Open a new terminal **in the root folder of the project, the same as where this README file is located**.

c) Run the script that will initialize the environment variables:

The script will prompt you to input the public ip/ url where the services will be exposed.

```bash
make install-environment-variables
```

## Supabase

1.  Open a terminal **in the root folder of the project, the same as where this README file is located** and run:

    ```bash
    make start-supabase
    ```

    This will start the supabase containers and show you the running logs. Once the supabase containers start running, they will start the internal process of setting up the database. This will take about 2-3 minutes.

2.  Verify the installation by navigating to the url configured in the file `supabase/.env` named as `SUPABASE_PUBLIC_URL` variable. This will
    take you to the supabase dashboard, which is enabled by default (you may disable it manually in the `supabase/docker-compose.yml` file if you want). To log in, you will need to use the `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` variables values that can be found in the `supabase/.env` file.

        You can check the `SERVICE_ROLE_KEY` created runing the following script:
        ```sh
        scripts/environment_variables/retrieve_anon_supabase.sh
        ```

3.  You may stop the containers by doing a `Control+C` in the terminal where you ran the `docker compose up ...` command or by running `docker compose down` after checking the setup.

## MongoDB

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and initialize the mongodb container:

   ```bash
   docker compose up mongodb
   ```

   Have a look at the logs and make sure everything is running smoothly.

   This will start the mongodb container. Wait a minute to make sure it has been properly initialized. After that, continue with the next step without stopping the container.

2. Initialize the database

   Open a terminal **in the root folder of the project, the same as where this README file is located** and run:

   ```bash
       make initialize_mongodb
   ```

3. After the initialization, you can run `docker compose down` to stop mongodb.

## Unstructured

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and initialize the unstructured container:

   ```bash
   docker compose up unstructured
   ```

   Have a look at the logs and make sure everything is running smoothly.

2. After the initialization, you can run `docker compose down` to stop unstructured.

## Weaviate

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and initialize the weaviate container:

   ```bash
   docker compose up weaviate
   ```

   Have a look at the logs and make sure everything is running smoothly.

2. Wait for about two minutes. After the initialization, you can run `docker compose down` to stop weaviate.

## Stackweb

The stackweb docker container requires some of the environment variables here defined to be built. This is why we need to source the .env file before building the image.

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and initialize the stackweb container:

   a) Source the stackweb environment variables:

   ```bash
   source stackweb/.env
   ```

   b) Build the docker image for stackweb:

   ```bash
   docker compose build stackweb
   ```

   The build process may take about 5 minutes depending on your internet connection and hardware.

## Stackend

1. Navigate to the `stackend` folder.

2. Configure the embedding models you want to use in the `stackend/embeddings_config.toml` file.

3. Configure the local LLM models you want to use in the `stackend/llm_local_config.toml` file and the `stackend/llm_config.toml` files.

4. Open a terminal **in the root folder of the project, the same as where this README file is located** and pull the backend containers.

   ```bash
   docker compose pull stackend celery_worker redis
   ```

5. Start the stackend service and run migrations:

   The database services need to be started first se we can run the migrations against them

   ```bash
   make start-supabase
   ```

   Then, open another terminal and start the stackend service:

   ```bash
   docker compose up stackend
   ```

   Wait for the stackend container to start. Then, on a new terminal, execute the following command to run the migrations:

   ```bash
   docker compose exec stackend bash -c "cd infra/migrations/postgres && alembic upgrade head"
   ```

## Stackrepl

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and pull the backend containers.

   ```bash
   docker compose build stackrepl
   ```

# Launch all services

1. Open a terminal **in the root folder of the project, the same as where this README file is located** and launch all services.

   ```bash
   docker compose up
   ```

2. Wait for about 2 minutes for everything to start. Then navigate to the url configured in the file `stackweb/.env` named as `NEXT_PUBLIC_URL` variable. You should see the StackAI landing page.

# SSL Setup

1. If you need to use SSL, configure the [Caddyfile](./caddy/Caddyfile) to use your certificates and keys.

# Domain Setup

You can configure custom domains for the three main services: the frontend application, the API, and the Supabase backend. We recommend using a primary domain and two subdomains.

For example:

- **APP URL**: `https://stackai.onprem.com`
- **API URL**: `https://api.stackai.onprem.com`
- **SUPABASE URL**: `https://db.stackai.onprem.com`

There are two steps to configure your domains:

### 1. Update Environment Variables

Run the following command and enter your domains when prompted. This command will update all the necessary `.env` files across the services.

```bash
make update-env-urls
```

### 2. Configure the Reverse Proxy

You also need to update the [Caddyfile](./caddy/Caddyfile) to reflect your new domains. Replace the placeholder domains in the file with the ones you have configured.

# Updates

In order to update the services, you will need to follow the instructions below:

1. Stop all the services with `docker compose stop`
2. Update the `image` field of the docker-compose.yml file of the service you want to update.

Example, to update the stackend service from `d3f54d3` to `f4c8aa0`
Usually you don't need to do this cause you use the latest version.

This line

```yaml
stackend:
  image: stackai.azurecr.io/stackai/stackend-backend:d3f54d3
```

Should be updated to:

```yaml
stackend:
  image: stackai.azurecr.io/stackai/stackend-backend:f4c8aa0
```

3. Pull the new images with

```bash
docker compose pull
```

In the case of the frontend (stackweb), you will need to rebuild the image with

```bash
docker compose build stackweb
```

4. Run database migrations if needed (instructions should be provided in the update README of the update)

```bash
docker compose up stackend
make run-postgres-migrations
```

5. Start all containers again with `docker compose up`
