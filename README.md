
# StackAI Docker Compose Deployment

This repository contains the configuration needed to run StackAI locally using docker compose.

# Requirements

- The script assume that you are running them on an Ubuntu machine.
- You will need internet access during the setup process.
- You need python 3.10 with pip and virtualenv installed.
- You will need docker and docker compose (compose version v2.26 or higher) installed in your machine. There is a script (see instructions below) that will install them for you if needed.
- You will need access to stackai's container image registry on Azure.
- Depending on how you configure the containers, different ports should be exposed, if you follow the default settings, the following ports need to be exposed:
  - Port 3000: TCP port used for the StackAI frontend HTTP
  - Port 8000: TCP port used for the StackAI backend HTTP
  - Port 8800: TCP port used for the Kong API Gateway HTTP
  - Port 8443: TCP port used for the Kong API Gateway HTTPS

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

## Set up the machine where you will run the deployment

You will need docker and docker compose installed in your machine. If you do not have them yet, there is a script in the `scripts` folder named `ubuntu_server_pre_setup.sh` that will install them for you.

To run them, open a terminal and navigate to the `scripts` folder:

```bash
cd scripts/docker
```
>
> :WARNING: As part of the setup process, your user will be added to the docker group, allowing you to run docker
> commands without using sudo. To make that change effective, the script will log you out from your current session.
> Log in right after and verify that you can run docker commands without using sudo.
>

Execute the script and log in again after it finishes:

```bash
./ubuntu_server_pre_setup.sh
```

## Install python, pip and virtualenv

Skip this section if you already have python, pip and virtualenv installed.

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

b) Open a new terminal and navigate to the `scripts/environment_variables` folder.

```bash
cd scripts/environment_variables
```

c) Run the script that will initialize the environment variables:

The script will prompt you to input the public ip/ url where the services will be exposed.

```bash
./create_env_files.sh
```

## Supabase

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and run:

    ```bash
    docker compose up studio kong auth rest realtime storage imgproxy meta functions analytics db vector supavisor 
    ```

    Once the supabase containers start running, they will start the internal process of setting up the database. This will take about 2-3 minutes.

2. Verify the installation by navigating to the url configured in the file `supabase/.env` named as `SUPABASE_PUBLIC_URL` variable. This will
take you to the supabase dashboard, which is enabled by default (you may disable it manually in the `supabase/docker-compose.yml` file if you want). To log in, you will need to use the `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` variables values that can be found in the `supabase/.env` file.

3. You may stop the containers by doing a `Control+C` in the terminal where you ran the `docker compose up ...` command or by running `docker compose down` after checking the setup.

## MongoDB

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and initialize the mongodb container:

    ```bash
    docker compose up mongodb
    ```

    Have a look at the logs and make sure everything is running smoothly.

    This will start the mongodb container. Wait a minute to make sure it has been properly initialized. After that, continue with the next step without stopping the container.

2. Get the connection string for your mongodb database

    The first thing you will need is to get the connection string for your mongodb database. To do so, open your `mongodb/.env` file and take the values for the `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` variables. Here is a template of what the connection string should look like (if using the default configuration):

    Replace `<username>` and `<password>` with the values got from your `mongodb/.env` file.

    ```bash
    mongodb://<username>:<password>@localhost:27017
    ```

    With the connection string in hand, you can initialize the database.

3. Initialize the database

    Open a new terminal and navigate to the `scripts/mongodb` folder:

    ```bash
        cd scripts/mongodb
    ```

    Run the initialization script:

    ```bash
    ./initialize_mongodb.sh
    ```

    In case the script errors with `permission denied`, run the following command:

    ```bash
    chmod +x initialize_mongodb.sh
    ```

    Then, run the script again.

4. After the initialization, you can run `docker compose down` to stop mongodb.

## Unstructured

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and initialize the unstructured container:

    ```bash
    docker compose up unstructured
    ```

    Have a look at the logs and make sure everything is running smoothly.

2. After the initialization, you can run `docker compose down` to stop unstructured.

## Weaviate

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and initialize the weaviate container:

    ```bash
    docker compose up weaviate
    ```

    Have a look at the logs and make sure everything is running smoothly.

2. Wait for about two minutes. After the initialization, you can run `docker compose down` to stop weaviate.

## Stackweb

The stackweb docker container requires some of the environment variables here defined to be built. This is why we need to source the .env file before building the image.

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and initialize the weaviate container:

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

3. Configure the local LLM models you want to use in the `stackend/llm_config.toml` file.

4. Open a terminal **in the root of folder of the project, the same as where this README file is located** and pull the backend containers.

    ```bash
    docker compose pull stackend celery_worker redis
    ```

5. Start the stackend service and run migrations:

    ```bash
    docker compose up stackend
    ```

    Wait for the stackend container to start. Then execute the following command to run the migrations:

    ```bash
    docker compose exec stackend bash -c "cd migrations/postgres && alembic upgrade head"
    ```

## Stackrepl

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and pull the backend containers.

    ```bash
    docker compose build stackrepl
    ```

# Launch all services

1. Open a terminal **in the root of folder of the project, the same as where this README file is located** and launch all services.

    ```bash
    docker compose up
    ```

2. Wait for about 2 minutes for everything to start. Then navigate to the url configured in the file `stackweb/.env` named as `NEXT_PUBLIC_URL` variable. You should see the StackAI landing page.

# SSL Setup

1. If you need to use SSL, configure the [Caddyfile](./caddy/Caddyfile) to use your certificates and keys.

# Updates

In order to update the services, you will need to follow the instructions below:

1) Stop all the services with `docker compose down`
2) Update the `image` field of the docker-compose.yml file of the service you want to update.

Example, to update the stackend service from `d3f54d3` to `f4c8aa0`

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

3) Pull the new images with

```bash
docker compose pull <name_of_the_service>
```

In the case of the frontend (stackweb), you will need to rebuild the image with `docker compose build stackweb`

4) Run database migrations if needed (instructions should be provided in the update README of the update)

```bash
docker compose up stackend
docker compose exec stackend bash -c "cd migrations/postgres && alembic upgrade head"
```

5) Start all containers again with `docker compose up`
