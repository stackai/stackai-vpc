
# StackAI local deployment using docker compose

# TODO

- [ ] Get supabase password and use the cli for the initial setup, otherwise, create a initialization script for the supabase database.
- [ ] Trim down supabase docker compose.yml file to only include the necessary services for the local deployment, there are a lot of services that are not needed.
- [ ] Remove supabase variables from NEXT_PUBLIC_* environment variables from the stackweb build process, as they make publishing the container images insecure. As a patch, add build arguments to the stackweb Dockerfile.
- [ ] Publish container images for stackend and stackweb to a private container registry so that they can be used in the local deployment instead of building them locally.
- [ ] Fix supabase signup in the local deployment.
- [ ] Fix supabase auth jwt generation process (broken on their website)
- [ ] Complete the mongodb initialization script ? (seems to be working, but check)

## KNOWN BUGS

- [ ] The document chunking preview does not work, the chunks are seen but the document is not. This is because somehow the frontend gets the url to call from the backend.

# Requirements

- You will need docker and docker compose (compose version v2.26 or higher) installed in your machine.

# Architecture description

## Supabase

Supabase is used as the application database, authentication and storage service. It is defined in the `supabase` folder.

### Services description

There following services are defined in the `docker-compose.yml` file of the `supabase` folder.

- `studio`: Supabase web interface.
- `kong`: A cloud-native API gateway, built on top of NGINX.
- `db`: The postgres database
- `auth`: Uses GoTrue for JWT authentication.
- `storage`: An S3-compatible object storage service that stores metadata in Postgres.
- `rest`: Turns the postgreSQL db into a GraphQL API (candidate for removal)
- `realtime`: A scalable websocket engine for managing user Presence, broadcasting messages, and streaming database changes (candidate for removal)
- `imgproxy`: IMG transformation and OCR service (candidate for removal)
- `meta`: A RESTful API for managing Postgres. Fetch tables, add roles, and run queries.
- `functions`: For supabase functions (candidate for removal)
- `analytics`: Analytics for the project (candidate for removal)
- `vector`: A vector database for storing embeddings (candidate for removal as we use weaviate)

### Networking

Kong is used as the API gateway for the supabase services. 
The internal connection URI for the supabase services is `http://kong:8000`. To avoid port conflicts with `stackend`, I have remapped the port to `8800` on the host machine, this means that the external (outside the docker network) connection URI for the supabase services is `http://0.0.0.0:8800`.

![Supabase architecture](docs/supabase-architecture.svg)

### Development notes

The supabase web interface that allows for `ANON_KEY` and `SERVICE_ROLE_KEY` generation, [see here](https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys), was broken as of 15/04/2024 the generated keys were not valid.

## MongoDB

The container for mongodb and its related configuration is defined on the `mongodb` folder.

### Services description

Two containers are setup in the `docker-compose.yml` file of the `mongodb` folder:

1. The `mongodb` container: This container is the main mongodb container. It is based on the `mongo` image and is setup to run as a single node replica set. It exposes the port `27017` to the host machine.
2. The `mongo-express` container: This container is a web interface for the mongodb database. It is based on the `mongo-express` image and is setup to connect to the `mongodb` container. It exposes the port `8081` to the host machine. The web interface can be accessed by navigating to `http://0.0.0.0:8081` on the host machine and using the credentials defined in the `mongodb/docker-compose.yml` file

### Networking

The `mongodb` URI that needs to be used with the current config is `"mongodb://mongodb:27017/?replicaSet=rs0`.

### MongoDB Initialization

The mongodb container needs to be initialized with some data for the application to work:

1. The `__models__` database that contains the templates for flow creation must be cloned from production to the local mongo database.

### Development notes

Setting up a mongodb single node replica set is a bit tricky, here are some notes on how to do it:

#### About the `host.docker.internal` host
To make the local deployment compatible with the use of websockets, a single node replica set is used. The main difficulty in doing this is seting up the network configuration in a way that allows the `motor` library to connect to the database.
If we setup the internal address of the mongodb container using `localhost` as the host, we will be able to connect to the database from another container using `mongodb` as the host, but `motor` will not be able to discover the internal representation
of the replica set, since we cannot jump to the `localhost` address of the mongodb container from another container.

To fix this issue, we need to use the special host `host.docker.internal` as the host for the mongodb container. This host is a special DNS name that resolves to the internal ip address of the host machine. This way, we can connect to the mongodb container from another container using `mongodb` as the host, and `motor` will be able to discover the internal representation of the replica set.

#### About the replica set initialization
To initialize a replica set, the `rs.initiate({_id:'rs0',members:[{_id:0,host:'host.docker.internal:27017'}]})` command must be run. This command must be run after the mongodb container is up and running, so we need to run it after the container is up and running.

To do this, we will take advantage of the healthcheck feature of the mongodb container. The healthcheck will run the `rs.initiate` command after the container is up and running, and will only stop the container if the command fails.

#### About authentication when using a replica set
In order to use authentication with the replica set configuration, we cannot just setup the `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` environment variables as the replica set crashes when the container starts. An additional configuration is needed to setup the replica set with authentication enabled, namely, we would need to create a keyfile, set it up in the container and then use the `mongod.conf` file to tell mongodb to use the keyfile for authentication.

## Stackweb

The stackweb service is the frontend of the stackai application. It is defined in the `stackweb.docker-compose.yml` file. To build it, clone the stackweb repository (see instructions below). This will be fixed by publishing the stackweb container image to a private container registry in the future.

### Services description

A single container is setup in the `stackweb.docker-compose.yml` file of the `stackweb` folder.

### Networking

The stackweb service is exposed to the host machine on port `3000`. The default connection URI (from within the docker network) is `http://stackweb:3000`. To connect from the host machine, navigate to `http://0.0.0.0:3000`.

## Stackend

The stackend service is the backend of the stackai application. It is defined in the `stackend.docker-compose.yml` file. To build it, clone the stackend repository (see instructions below). This will be fixed by publishing the stackend container image to a private container registry in the future.

### Services description

The stackend service is composed of four containers:
- `redis`: A redis instance that is used by celery to store the task queue.
- `celery_worker`: A celery worker that processes the tasks in the task queue.
- `flower`: A web interface for the celery worker.
- `stackend`: The main stackend service.

### Networking

- The stackend service is exposed to the host machine on port `8000`. The default connection URI (from within the docker network) is `http://stackend:8000`. To connect from the host machine, navigate to `http://0.0.0.0:8000`.
- Flower is indeed exposed to the host machine on port `5555`. The web interface can be accessed by navigating to `http://0.0.0.0:5555` on the host machine.
- Redis is not exposed to the host machine, it is only used by the stackend service.
- Celery worker is not exposed to the host machine, it is only used by the stackend service.


## Unstructured

The unstructured service is used for document parsing. It is defined in the `unstructured` folder.

### Services description

One container is setup in the `docker-compose.yml` file of the `unstructured` folder.

### Networking

The unstructured service is not exposed to the host machine, it is only used by the stackend service.

The internal connection URI (from within the docker network) is `http://unstructured:8000/general/v0/general`.

## Weaviate

Weaivate is the vector database used by the stackend service. It is defined in the `weaviate` folder.

### Services description

A single container is setup in the `docker-compose.yml` file of the `weaviate` folder. No authentication is setup for the weaviate service.

### Networking

The weaviate service is not exposed to the host machine, it is only used by the stackend service.

The default connection URI (from within the docker network) is `http://weaviate:9090`, (no authentication is setup).

## 1. Create your .env files and initialize your secrets

### Supabase secrets

Go to the `supabase` folder and copy the `.env.example` file renaming it as `.env`.

After that, fill in the `secrets` section of the `.env` file, to do so, you will need to generate a new set of secrets following the process of the [supabase docker self hosting documentation](https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys).

#### :warning: HACK WARNING :warning:

Last time I checked, the ANON_KEY and SERVICE_ROLE_KEY generation process was broken. Continue with the default ones in the `.env.example` file if you do not want to go into the rabbit hole of fixing it.

You will need to fill the value of `ANON_KEY` and `SERVICE_ROLE_KEY` in other places as well (see below).

### Stackweb .env file

Copy `.env.template` and rename it to `.env` in the root folder of this project. Fill in the values for the missing variables. Beware that you should not use the production `SUPABASE_ANON_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` here, they wont work!

There is a reason why this file is named `.env` instead of `.env.stackweb` or something alike. By using `.env` the `docker-compose` command will automatically source the variables from this file when building the `stackweb` container and insert them into the build arguments.

### Stackend stackend.env file

Copy `stackend.env.template` and rename it to `stackend.env` in the root folder of this project. Fill in the values for the missing variables. Beware that you should not use the production `SUPABASE_ANON_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` here, they wont work!

## 2. Clone the stackend and stackweb repositories

They should be cloned in the same directory as this file.

```bash
git clone git@github.com:stackai/stackweb.git
git clone git@github.com:stackai/stackend.git
```

### :warning: HACK WARNING :warning:: Patch the stackweb Dockerfile and set the NEXT_PUBLIC_* environment variables

You will need to patch the `stackweb` Dockerfile in order to set the `NEXT_PUBLIC_*` environment variables to work properly with the local deployment. This is a temporal hack and needs to be fixed in the future. Inside the Dockerfile, go to the `RUN npm run buil` line, and copy paste the following lines before it: 

```text
ARG NEXT_PUBLIC_HF_API_KEY
ARG NEXT_PUBLIC_MONGODB_PWD
ARG NEXT_PUBLIC_NOTION_OAUTH_CLIENT_ID
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SUPABASE_URL
```

Those lines will allow us to set the proper build arguments when building the stackweb container (they will be sourced in the `stackweb.docker-compose.yml` from the `.env` file).

## 3. Build all docker containers

```bash
docker-compose build
```

## 4. Initialize mongodb database

First, start the mongodb container:

```bash
docker compose up mongodb
```

Run the initialization container in another terminal, it will prompt you for the production database URI (hint: use your `MONGODB_URI` secret)

```bash
docker compose up -d mongodb_init
docker exec -it mongodb_init bash -c "python /app/init_db.py"
```

Then remove the initialization container:

```bash
docker compose down mongodb_init -t 1
```

Check the databases using mongo-express, to do so, start the mongo-express container:

```bash
docker compose up mongo-express
```

Wait for about 5 to 10 seconds. Then navigate to `http://0.0.0.0:8081` on your browser and login using the credentials defined in the `mongodb/docker-compose.yml` file.

## 5. Initialize supabase database

### :warning: HACK WARNING :warning:: This should be done with a script based on the supabase cli, but we do not have access to that cli atm

First, start the supabase containers:

```bash
cd supabase && docker compose up
```

Then, navigate to the supabase dashboard on `http://0.0.0.0:8800` on your browser and login using the credentials defined in the `supabase/.env` file.

To initialize the database, you will need to create the tables, functions, triggers and webhooks manually (IN THAT ORDER). To help you with that, you open the file `supabase/initialization/` folder and copy-paste the contents of each file into the supabase dashboard SQL editor. This will create the tables, functions and triggers of the production db with the schema that was used as of April 15, 2024. Then, create the webhook manually (see below)

Steps:

1. Create the tables (skip if you have already have them) based on the production database schema.
 - Go to the dashboard for the production deployment of supabase, navigate to the `stackweb` project.
 - For each table, click on `Definition`, this will give you the SQL definition of the table.
 - Go to the local deployment dashboard, navigate to SQL editor and paste the SQL definition of the table.
 - Keep in mind that the tables need to be created in a certain order, otherwise an error will be thrown.
2. Add functions.
 - On the supabase production deployment, navigate to `Database` and then to `Functions`.
 - Copy the function definition, open the advanced tap to see if the function is a `DEFINER` or an `INVOKER`, and the expected return type. Then, go to  `edit function` by clicking on the three dots on the right of the function name and copy its SQL definition.
 - For each function, go to the local deployment dashboard, navigate to `Database`, `Functions` and click on `Create a new function`, use the `show advanced settings` panel to set the propper security type and paste the SQL definition of the function. Dont forget about the return type.
3. Add triggers.
  - On the supabase production deployment, navigate to `Database` and then to `Triggers`.
  - Go to `edit trigger` by clicking on the three dots on the right of the trigger name and take a look at its values.
  - On the local deployment dashboard, navigate to `Database`, `Triggers` and click on `Create a new trigger` and fill in the values.
4. Add webhooks.
 - On the supabase production deployment, navigate to `Database` and then to `Webhooks`.
 - Go to `edit webhook` by clicking on the three dots on the right of the webhook name and take a look at its values.
 - On the local deployment dashboard, navigate to `Database`, `Webhooks` and click on `Create a new webhook` and fill in the values. Important, set the webhook url to point to stackend, in the case of this specific configuration, that url is `http://stackend:8000/webhooks/new_user`, do not use the production url.
  
## 6. Start all services
    
```bash
docker-compose up
```

Go to `http://0.0.0.0:3000` to access the stackweb frontend.

To stop all services, run:

```bash
docker-compose down
```
