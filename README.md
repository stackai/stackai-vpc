
# StackAI Docker Compose Deployment

# Requirements

- You will need docker and docker compose (compose version v2.26 or higher) installed in your machine.

# Set up process

Follow the instructions in the order they are presented.

## Set up the machine where you will run the deployment

Run the script in the `scripts` folder named `ubuntu_server_pre_setup.sh` to install docker and docker compose.

## MongoDB

1. Go to the `mongodb` folder and create your mongodb credentials.

    a) Copy the `.env.example` file and rename it as `.env`.
    b) Fill in the variables with your own values. Do not use the default ones.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up mongodb
    ```

3. Once the database is running, run the initialization scripts.

    a) Read more in the [MongoDB initialization README](mongodb/initialization/README.md)

## Unstructured

1. Go to the `unstructured` folder and create your unstructured credentials.

    a) Copy the `.env.example` file and rename it as `.env`.
    b) Fill in the variables with your own values. Do not use the default ones.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up unstructured
    ```

## Weaviate

1. Go to the `weaviate` folder and create your weaviate credentials. This will be used to authenticate your requests to your local weaviate instance.

    a) Copy the `.env.example` file and rename it as `.env`.
    b) Fill in the variables with your own values. Do not use the default ones.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up weaviate
    ```

## Supabase

1. Go to the `supabase` folder and create your supabase credentials.
    a) Copy the `.env.example` file and rename it as `.env`.
    b) Read the [Supabase README](supabase/README.md) to learn how to fill the values.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up supabase
    ```

    Once the supabase containers start running, they will start the internal process of setting up the database. This will take about 2-3 minutes.

3. Verify the installation by navigating to the url configured in `SUPABASE_PUBLIC_URL`. If you have not disabled the dashboard you should be able to log in and see that the tables have been created.

## Clone the stackend, stackweb and stackrepl repositories

They should be cloned in the same directory as this file.

:warning: COPY PASTE WARNING :warning:

- If you copy paste the repos from an existing folder remember to remove your .env file and the node_modules, .next, cache etc folders!!!

```bash
git clone git@github.com:stackai/stackweb.git
git clone git@github.com:stackai/stackend.git
git clone git@github.com:stackai/stackrepl.git
```

### :warning: HACK WARNING :warning: Change the port of the stackrepl container to 7777

In the stackrepl/Dockerfile, edit the end of the file to:

```Dockerfile
EXPOSE 7777
ENV PORT 7777

CMD ["python3.10","-m","uvicorn", "server.api:app", "--host", "0.0.0.0", "--port", "7777"]
```

## Stackweb

1. Copy the `.env.template` file and rename it as `.env` in the root folder of this project. Fill in the values for the missing variables.
   - Make sure to replace the supabase anon and service role keys with the ones you created in the supabase section.
   - Replace the values for the api keys that you intend to use.

2. In the .env file, replace the `TIPTAP_PRO_TOKEN` with your own tiptap pro token. This is needed to build the frontend.

3. Copy the .env file and paste it in the `stackweb` folder. Do not move the file, make a copy, we need both.

4. Open a terminal in **this folder** and run:
    Source the .env file:

    ```bash
    source .env
    ```

    Build the docker image for stackweb:

    ```bash
    docker compose build stackweb
    ```

## Stackend

1. Copy the `stackend.env.template` file and rename it as `stackend.env` in the root folder of this project. Fill in the values for the missing variables.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose build stackend
    ```

## SSL Setup

1. If you need to use SSL, configure the [Caddyfile](./caddy/Caddyfile) to use your certificates and keys.
