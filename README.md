
# StackAI Docker Compose Deployment

# Requirements

- You will need docker and docker compose (compose version v2.26 or higher) installed in your machine.
- You will need access to stackai's container image registry on Azure.
- Depending on how you configure the containers, different ports should be exposed, if you follow the default settings, the following ports need to be exposed:
  - Port 3000: TCP port used for the StackAI frontend
  - Port 8000: TCP port used for the StackAI backend
  - Port 8800: TCP port used for the Kong API Gateway
  - Port 8443: TCP port used for the Kong API Gateway

If you set up the Caddy reverse proxy (See steps below), you may change the ports above for the ports 80 or/and 443.

# Set up process

Follow the instructions in the order they are presented.

## Set up the machine where you will run the deployment

You will need docker and docker compose installed in your machine. If you do not have them yet, there is a script in the `scripts` folder named `ubuntu_server_pre_setup.sh` that will install them for you.

To run them, open a terminal in the `scripts` folder and run:

```bash
./ubuntu_server_pre_setup.sh
```

## Log in to StackAI's Container Registry

You will need to log in to StackAI's container registry on Azure to pull the images we provided you with.

```bash
docker login -u <the_username_we_provided_you_with> -p <the_password_we_provided_you_with> stackai.azurecr.io
```

## Create all .env files

Run the following command to create all the .env from their templates in all folders. The template values are meant to be replaced with your own credentials. :warning: DO NOT USE THE DEFAULT VALUES FOR YOUR SECRETS/API KEYS. :warning:

Go to the `scripts` folder and run:

```bash
./create_env_files.sh
```

## Supabase

1. Go to the `supabase` folder and create your supabase credentials.
    a) Read the [Supabase README](supabase/README.md) to learn how to fill the values in the .env file.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up studio kong auth rest realtime storage imgproxy meta functions analytics db vector supavisor 
    ```

    Once the supabase containers start running, they will start the internal process of setting up the database. This will take about 2-3 minutes.

3. Verify the installation by navigating to the url configured in `SUPABASE_PUBLIC_URL`. If you have not disabled the dashboard you should be able to log in and see that the tables have been created.

4. You may run `docker compose down` after checking the setup.

## MongoDB

1. Go to the `mongodb` folder and create your mongodb credentials.

    a) Fill in the variables in the .env file with your own values. Do not use the default ones.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up mongodb
    ```

3. Once the database is running, run the initialization scripts.

    a) Read more in the [MongoDB initialization README](mongodb/initialization/README.md)

4. After the initialization, you can run `docker compose down` to stop mongodb.

## Unstructured

1. Go to the `unstructured` folder and create your unstructured credentials.

    a) Fill in the variables in the .env file with your own values. Do not use the default ones (copied from the template.)

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up unstructured
    ```

3. After the initialization, you can run `docker compose down` to stop unstructured.

## Weaviate

1. Go to the `weaviate` folder and create your weaviate credentials. This will be used to authenticate your requests to your local weaviate instance.

    a) Fill in the variables in the .env file with your own values. Do not use the default ones copied from the template.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up weaviate
    ```

3. Wait for about 2 minutes for everything to start up. If the startup is successful, you can run `docker compose down` to stop weaviate.

## Stackweb

The stackweb docker container requires some of the environment variables here defined to be built. This is why we need to source the .env file before building the image.

1. Navigate to the `stackweb` folder.

2. Fill in the values for the missing variables in the .env file.
   - Make sure to replace the supabase anon and service role keys with the ones you created in the supabase section.
   - Replace the values for the api keys that you intend to use.

4. Open a terminal in **this folder** and run:

    Build the docker image for stackweb:

    ```bash
    source stackweb/.env
    docker compose build stackweb
    ```

    The build process may take about 5 minutes depending on your internet connection and har

## Stackend

1. Navigate to the `stackend` folder.

2. Fill in the values for the missing variables in the .env file.

3. Configure the embedding models you want to use in the `stackend/embeddings_config.toml` file.

4. Configure the local LLM models you want to use in the `stackend/llm_config.toml` file.

5. Open a terminal in **this folder** and run:

    ```bash
    docker compose pull stackend celery_worker redis
    ```

## Stackrepl

1. Navigate to the `stackrepl` folder.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose build stackrepl
    ```

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

4) Run database migrations if needed (they should be provided in the update package)

5) Start the services again with `docker compose up <name_of_the_service>`
