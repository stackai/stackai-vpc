
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
    b) Fill in the variables with your own values. Do not use the default ones.

2. Open a terminal in **this folder** and run:

    ```bash
    docker compose up supabase
    ```

    Once the supabase containers start running, they will start the internal process of setting up the database. This will take about 2-3 minutes.

3. Initialize the supabase database.

    Read the [Supabase initialization README](supabase/initialization/README.md) and follow the instructions detailed there to initialize the database.

## KNOWN BUGS

- [ ] The document chunking preview does not work, the chunks are seen but the document is not. This is because somehow the frontend gets the url to call from the backend.

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

:warning: A tip to see the SQL commands needed to create the tables, functions and triggers is to go to the production supabase dashboard, navigate to the `stackweb` project, and then to the `Backup` tab. There you can download a dump of the production db. Extract it and open it with a text editor (i recommend something like `vim` or `neovim` as it quite large) to see the commands.

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

## 0. If you are trying to set up a EC2 instance to build a stack AMI, first execute the setup script

Go to the `scripts` folder and first READ and then execute the `ubuntu_server_pre_setup.sh` script to install docker, setup github, and pull the repos

# :warning: Before publishing the AMI, do not forget to remove the ssh keys to your account both in the image and in the github webpage so no one can login to our github with them

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

## 2. Clone the stackend, stackweb and stackrepl repositories

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

## 3. Build all docker containers

```bash
docker compose build
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

## 5. Initialize supabase database & storage buckets

### :warning: HACK WARNING :warning:: This should be done with a script based on the supabase cli, but we do not have access to that cli atm

First, start the supabase containers:

```bash
cd supabase && docker compose up
```

Then, navigate to the supabase dashboard on `http://0.0.0.0:8800` on your browser and login using the credentials defined in the `supabase/.env` file.

To initialize the database, you will need to:

1. Create the tables
2. Create the functions
3. Create the triggers
4. Create row level security
5. Prepopulate the tables (as of now, only the roles table needs to be prepopulated)

To help you with that, you open the file `supabase/initialization/` folder and copy-paste the contents of the remote schema file into the supabase dashboard SQL editor.

To generate the remote schema file, the following command was used:

Create a temporal folder.

```bash
mkdir temporal && cd temporal
```

Initialize the supabase project.

```bash
supabase init
```

Start the containers

```bash
supabase start
```

Link the project to our prod supabase db.

```bash
supabase link
```

Pull the schema from our production supabase db. If you get an error, run the migration repair.

```bash
supabase db pull
```

Run the migration to update the schema. If you get a manifest error, you may need to update the version of the associated service in the temporal/supabase/.temp/<service_name> file.

```
supabase migration up
```

```bash
supabase db pull --schema public,auth,storage
```

The schema migrations files will be present inside the migrations folder.

:warning: Adjust any webhooks to point to the local stackend service :warning:

For example, the add_user_to_org_sso points to the production stackend service when creating the migration schema, we need to adjust it here!

After that, run the query in the `prepopulate.sql` file in the supabase studio UI to initialize the database.

### For the storage buckets

Go to the production dashboard and navigate to the storage section. Replicate the necessary buckets. Some of the most important ones are:

```

user_documents
indexed_documents
dataframes

```

Replicate them in docker's supabase.

### :warning: TO-DO: Create a script that does this for you if we cannot do it from supabase cli in the near future

## 6. Start all services

```bash
docker compose up
```

Go to `http://0.0.0.0:3000` to access the stackweb frontend.

To stop all services, run:

```bash
docker compose down
```
