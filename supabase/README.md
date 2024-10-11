# Supabase Docker Containers

This directory contains the Docker Compose configuration for running Supabase locally.

## Set Up Instructions

You will need to copy the `.env.example` file to `.env` and fill in the values. To do so, you will need to do the following:

### Getting your own credentials

Follow the instructions [here](get_secrets/README.md) to generate your own credentials. This is a very important step to ensure the security of your databases. DO NOT USE THE DEFAULT CREDENTIALS IN A PRODUCTION ENVIRONMENT. The credentials will be written to the `.env` file in the `get_secrets` directory. [Link to the file (after being generated](get_secrets/.env).

### Setting up networking

Without SSL/TLS:
>
> An static IP is recommended for this setup.
>
> If you intend to run the whole stack on your local machine, you can use your local IP instead of a public static IP.
> To get your local IP, you can run `ipconfig` (on Windows) or `ifconfig` (on macOS/Linux) and select your address in your wifi network.
>

- Set `SITE_URL` to point to the IP/domain where you will be running the frontend containers. If you are using a single machine to do the setup without SSL, it will likely be `http://<your-ip>:3000`.

- Point the `API_EXTERNAL_URL` to the IP/domain where you will be running the code in this repository folder (supabase). If you are using a single machine to do the setup without SSL, it will likely be `http://<your-ip>:8800`.

- Point the `SUPABASE_PUBLIC_URL` to the IP/domain where you will be hosting the Studio Dashboard. If you are using a single machine to do the setup without SSL, it will likely be `http://<your-ip>:8800`.

With SSL/TLS:
>
> This setup requires configuring the Caddy reverse proxy, which is in charge of handling SSL/TLS termination.
> The specific setup will depend on what you want your set up to be (subdomain of your main domain, separate domain, etc.).
>
- Point the `SITE_URL` to the domain where you will be running the frontend containers. This will probably look like `https://stackai.your-domain.com`.

- Point the `API_EXTERNAL_URL` to the domain where you will be running the code in this repository folder (supabase). This will probably look like `https://stackdbs.your-domain.com`.

- Point the `SUPABASE_PUBLIC_URL` to the domain where you will be hosting the Studio Dashboard. This will probably look like `https://stackdb.your-domain.com`. The supabase dashboard is a web UI for managing your databases, and it will be served from this domain.
