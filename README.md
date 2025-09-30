# StackAI Docker Compose Deployment

This repository contains the configuration needed to run StackAI locally using docker compose.

# Requirements

## Hardware

1. At least 64GB of RAM
2. At least 16 CPU cores
3. 1TB of disk space

## Software

- Ubuntu 24.04 LTS
- Python 3.10 or higher.
- You will need internet access during the setup process.
- Docker and Docker Compose (compose version v2.26 or higher). Follow instructions below to install them if needed.

Check the steps below for instructions on how to check if you meet this requirement.

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

**Note:** Throughout this setup guide, when you see `cd /path/to/stackai-onprem`, replace `/path/to/stackai-onprem` with the actual path to where you have cloned or downloaded this repository on your system.

## Install make

```bash
# linux
sudo apt install make
# RHEL
sudo dnf install make
```

Make sure that make is installed correctly by running:

```bash
make --version
```

## Set up the machine where you will run the deployment

You will need docker and docker compose installed in your machine.

To install them, open a terminal and navigate to the root folder of the project by running:

```bash
cd /path/to/stackai-onprem
```

Then execute the following command, log in again after it finishes:

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
# linux
sudo apt update
# RHEL
sudo dnf update
```

Install python3, pip and virtualenv:

```bash
# linux
sudo apt install python3-pip python3-venv
# RHEL
sudo dnf install python3.11 python3.11-pip
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

Ensure that python is installed and working correctly. Start by making sure that the python version is >= 3.10:

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

### Instructions

#### 1. Open a new terminal and navigate to the root folder of the project:

```bash
cd /path/to/stackai-onprem
```

#### 2. Run the script that will initialize the environment variables:

The script will prompt you to input the public ip/ url where the services will be exposed.

```bash
make install-environment-variables
```

#### 3. Domain Setup

You can configure custom domains for the three main services: the frontend application, the API, and the Supabase backend. We recommend using a primary domain and two subdomains.

For example:

- **APP URL**: `https://stackai.onprem.com`
- **API URL**: `https://api.stackai.onprem.com`
- **SUPABASE URL**: `https://db.stackai.onprem.com`

There are two steps to configure your domains:

##### 3.1 Update Environment Variables

Run the following command and enter your domains when prompted. This command will update all the necessary `.env` files across the services.

```bash
make configure-domains
```

##### 3.2 Configure the Reverse Proxy

You also need to update the [Caddyfile](./caddy/Caddyfile) to reflect your new domains. Replace the placeholder domains in the file with the ones you have configured.

#### 5. Start application:

```bash
docker compose up -d
```

#### 4. Run migrations:

```bash
make run-postgres-migrations
make run-template-migrations
```

# Updates

In order to update the services, you will need to follow the instructions below:

1. Stop all the services with `docker compose stop`
2. Update the `image` field of the docker-compose.yml file of the service you want to update.

Example, to update the stackend service from `v1.0.0` to `v1.0.1`
Usually you don't need to do this cause you use the latest version.

This line

```yaml
stackend:
  image: stackai.azurecr.io/stackai/stackend-backend:v1.0.0
```

Should be updated to:

```yaml
stackend:
  image: stackai.azurecr.io/stackai/stackend-backend:v1.0.1
```

3. Pull the new images with

```bash
docker compose pull
docker compose up
```

In the case of the frontend (stackweb), you will need to rebuild the image with

```bash
docker compose down stackweb
source stackweb/.env
docker compose build stackweb
docker compose up stackweb
```

4. Run database migrations if needed

```bash
make run-postgres-migrations
make run-template-migrations
```

# FAQ

## How to configurate LLMs?

1. Navigate to the `stackend` folder.
2. Configure the embedding models you want to use in the `stackend/embeddings_config.toml` file.
3. Configure the local LLM models you want to use in the `stackend/llm_local_config.toml` file and the `stackend/llm_config.toml` files.
4. Restart the services that depend on this configuration

### How to activate SSO?

1. Run `make saml-enable`. This will config the SAML configuration.
2. Run `make saml-status`. This will give you the SAML configurations you need to setup in your IdP (Identity Provider)

#### Register Providers

1. Run `make saml-add-provider metadata_url='{idp-metadata-ur}' domains='{comma-sepparated-domains}'`
2. You can list profviders running `make saml-list-providers`
3. You can delete providers running `make saml-delete-provider provider_id='{provider-id}'`

```bash
docker compose dow stackend celery_worker
docker compose up stackend celery_worker
```
