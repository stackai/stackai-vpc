# Stack AI December Update

# Main New Features

- LLMs now can use tools.
- Parallel workflow execution
- Templated output node
- New dashboard design.
- Personal folders for each user.
- New chat interface.
- New agent builder mode.
- Output templates.

# Update Procedure

## Expose the port 9000 of the virtual machine running the stack server

We have added a new service to the supabase containers called `minio`. This service is used to expose the content of the `stack-ai-usercontent` bucket to the frontend so that features like Chart generation work on-premise. The service is configured to
run on port 9000 of the virtual machine, you will need to expose this port for it to work properly.

## Create new environment variables

Create a random passowrd that will be used for your private MinIO (s3 compatible object storage service) service:

Go to the `supabase/.env` file and add the following variable:

```
MINIO_PASSWORD="super-secret-password"
```


Get the public IP or the public url of the virtual machine running the stack server.

Go to the `stackend/.env` file, locate the section where the S3 variables are defined.

Copy the following variables, replacing the values of `{{VIRTUAL_MACHINE_IP_OR_URL}}` and `{{MINIO_PASSWORD}}` with their actual values:

```jinja
S3_ENDPOINT_URL="http://{{VIRTUAL_MACHINE_IP_OR_URL}}:9000"
S3_USERCONTENT_PUBLIC_BUCKET=stack-ai-usercontent
S3_AWS_ACCESS_KEY="supa-storage"
S3_AWS_REGION="us-east-1"
S3_AWS_SECRET_ACCESS_KEY="{{MINIO_PASSWORD}}"
```

Where:
- `{{VIRTUAL_MACHINE_IP_OR_URL}}` is the public IP or the public url of the virtual machine running the stack server.
- `{{MINIO_PASSWORD}}` is the password you created in the first step for the MinIO service.


## Execute the update script

Open a terminal inside the update folder and run the following commands:

1) Give execute permissions to the update script:

```bash
chmod +x run_update.sh
```

2) Run the update script:

```bash
./run_update.sh
```
