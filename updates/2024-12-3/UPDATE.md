# Stack AI December Update

## 1. Stop the frontend and backend service containers

Open a terminal in the root folder of your on-premise deployment folder and run the following commands:

```bash
docker compose stop stackweb stackend celery_worker
```

## 2. Update the frontend container

Open the folder containing your stack-ai on-premise deployment.

1) Replace the files in `stackweb/` with the ones in `<update_folder>/stackweb/`.

2) Add the following environment variable to the stackweb/.env file of your deployment, only substituting the placeholder value with your own if you actually have a sharepoint client id:

```
NEXT_PUBLIC_SHAREPOINT_CLIENT_ID="<your-sharepoint-client-id>"
```

3) Build the frontend container:

```bash
source stackweb/.env
```

```bash
docker compose build stackweb
```

## 3. Update the backend docker images

Open a terminal in the root folder of your on-premise deployment and run the following command:

```bash
docker compose pull stackend celery_worker
```

## 4. Execute the update script

Open a terminal inside the update folder and run the following commands:

1) Give execute permissions to the update script:

```bash
chmod +x run_update.sh
```

2) Run the update script:

```bash
./run_update.sh
```

## 5. Run database migrations

Start the stackend service:
```bash
docker compose up -d stackend
```

Once all containers are running, run the following command to apply any pending migrations:

```bash
    docker compose exec stackend bash -c "cd infra/migrations/postgres && alembic upgrade head"
```

## 6. Start all services

Open a terminal in the root folder of your on-premise deployment and run the following command:

```bash
docker compose up
```
