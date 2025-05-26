import base64
import os
import secrets
import string
import time
from pathlib import Path
from typing import Dict

import jwt
from jinja2 import Environment, FileSystemLoader, Template

environment = Environment(loader=FileSystemLoader("templates/"))

def get_env_var_by_env_file(var_name: str, env_file: str) -> str | None:
    """Get the value of an environment variable from a given .env file."""
    path = Path(env_file)
    if not path.is_file():
        return None # return None if the file does not exist

    for line in path.read_text().splitlines():
        if line.startswith(f"{var_name}="):
            return line.partition("=")[2].strip()
    return None

def generate_password(length: int = 32) -> str:
    """Generate a random password of the given length."""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt(role: str, secret: str) -> str:
    """Generate a JWT token for the given role and secret."""
    iat = int(time.time())
    exp = iat + (5 * 365 * 24 * 60 * 60)  # 5 years from now
    payload = {"role": role, "iss": "supabase", "iat": iat, "exp": exp}
    return jwt.encode(payload, secret, algorithm="HS256")


def get_supabase_template_variables(virtual_machine_ip_or_url: str) -> Dict[str, str]:
    """Get the template variables for the supabase template.

    Args:
        virtual_machine_ip_or_url: The IP or URL of the virtual machine where supabase will be hosted.
    """

    # Generate PostgreSQL password
    psql_password = get_env_var_by_env_file("POSTGRES_PASSWORD", "stackend/.env") or generate_password()

    # Generate JWT secret
    jwt_secret = get_env_var_by_env_file("JWT_SECRET", "supabase/.env") or generate_password(40)

    # Generate anon and service role keys
    anon_key = get_env_var_by_env_file("ANON_KEY", "supabase/.env") or generate_jwt("anon", jwt_secret)
    service_role_key = get_env_var_by_env_file("SERVICE_ROLE_KEY", "supabase/.env") or generate_jwt("service_role", jwt_secret)

    # Generate a password for the supabase dashboard
    dashboard_password = get_env_var_by_env_file("DASHBOARD_PASSWORD", "supabase/.env") or generate_password(length=16)

    # Generate Logflare keys
    logflare_logger_backend_api_key = get_env_var_by_env_file("LOGFLARE_LOGGER_BACKEND_API_KEY", "supabase/.env") or generate_password()
    logflare_api_key = get_env_var_by_env_file("LOGFLARE_API_KEY", "supabase/.env") or generate_password()

    # Generate a password for the minio service
    minio_password = get_env_var_by_env_file("MINIO_PASSWORD", "stackend/.env") or generate_password()

    return {
        "POSTGRES_PASSWORD": psql_password,
        "JWT_SECRET": jwt_secret,
        "ANON_KEY": anon_key,
        "SERVICE_ROLE_KEY": service_role_key,
        "DASHBOARD_USERNAME": "admin",
        "DASHBOARD_PASSWORD": dashboard_password,
        "LOGFLARE_LOGGER_BACKEND_API_KEY": logflare_logger_backend_api_key,
        "LOGFLARE_API_KEY": logflare_api_key,
        "VIRTUAL_MACHINE_IP_OR_URL": virtual_machine_ip_or_url,
        "MINIO_PASSWORD": minio_password,
    }


def get_weaviate_template_variables() -> Dict[str, str]:
    """Get the template variables for the weaviate template."""
    api_key = get_env_var_by_env_file("WEAVIATE_API_KEY", "stackend/.env") or generate_password(length=12)
    api_key_user = get_env_var_by_env_file("WEAVIATE_API_KEY_USER", "stackend/.env") or "jhondoe@example.com"
    return {
        "WEAVIATE_API_KEY": api_key,
        "WEAVIATE_API_KEY_USER": api_key_user,
    }


def get_mongodb_template_variables() -> Dict[str, str]:
    """Get the template variables for the mongodb template."""
    root_password = get_env_var_by_env_file("MONGODB_ROOT_PASSWORD", "mongodb/.env") or generate_password(length=12)
    root_username = get_env_var_by_env_file("MONGODB_ROOT_USERNAME", "mongodb/.env") or "stack_user"
    return {
        "MONGODB_ROOT_USERNAME": root_username,
        "MONGODB_ROOT_PASSWORD": root_password,
    }


def get_unstructured_template_variables() -> Dict[str, str]:
    """Get the template variables for the unstructured template."""
    api_key = get_env_var_by_env_file("UNSTRUCTURED_API_KEY", "unstructured/.env") or generate_password(length=12)
    return {
        "UNSTRUCTURED_API_KEY": api_key,
    }


def get_stackrepl_template_variables() -> Dict[str, str]:
    """Get the template variables for the stackrepl template."""
    return {}


def get_stackend_template_variables(
    mongodb_uri: str,
    supabase_anon_key: str,
    supabase_service_role_key: str,
    postgres_password: str,
    unstructured_api_key: str,
    weaviate_api_key: str,
    virtual_machine_ip_or_url: str,
    stackai_licence: str,
    minio_password: str,
) -> Dict[str, str]:
    """Get the template variables for the stackend template."""
    connection_encryption_key = base64.b64encode(os.urandom(32)).decode()

    return {
        "ANON_KEY": supabase_anon_key,
        "STACKAI_LICENCE": stackai_licence,
        "SERVICE_ROLE_KEY": supabase_service_role_key,
        "ENCRYPTION_KEY": connection_encryption_key,
        "MONGODB_URI": mongodb_uri,
        "POSTGRES_PASSWORD": postgres_password,
        "UNSTRUCTURED_API_KEY": unstructured_api_key,
        "WEAVIATE_API_KEY": weaviate_api_key,
        "VIRTUAL_MACHINE_IP_OR_URL": virtual_machine_ip_or_url,
        "MINIO_PASSWORD": minio_password,
    }


def get_stackweb_template_variables(
    virtual_machine_ip_or_url: str,
    supabase_anon_key: str,
    supabase_service_role_key: str,
) -> Dict[str, str]:
    """Get the template variables for the stackweb template."""
    return {
        "VIRTUAL_MACHINE_IP_OR_URL": virtual_machine_ip_or_url,
        "ANON_KEY": supabase_anon_key,
        "SERVICE_ROLE_KEY": supabase_service_role_key,
    }


def render_and_save_template(
    template: Template,
    variables: Dict[str, str],
    template_folder_path: Path,
    template_file_name: str,
) -> None:
    """Renders the template and saves it to the given file overwriting it if it exists."""
    filled_in_template = template.render(**variables)
    with open(template_folder_path / template_file_name, "w") as f:
        f.write(filled_in_template)


def get_virtual_machine_ip_or_domain() -> str:
    """Get the IP or URL of the virtual machine where the supabase studio dashboard will be hosted."""

    while True:
        virtual_machine_ip_or_domain = input(
            """
Please, enter the IP or URL of the virtual machine that will be used to host all the services. This is the ip/domain that
your users will need to input in their browser to access StackAI. 

!!! DO NOT ADD ANY PORT NUMBER TO THE IP/URL !!!

Example values: 43.168.4.99 or stackai.your-domain.com

[INPUT] > """
        )
        if virtual_machine_ip_or_domain:
            print(
                f"~> We will use the following IP/URL (please ensure it is valid): {virtual_machine_ip_or_domain}"
            )
            return virtual_machine_ip_or_domain
        else:
            print("Invalid input. Please, try again.")


def get_licence_key() -> str:
    """Get the licence key from the user."""
    while True:
        licence_key = input("Please, input your Stack AI licence key: ")
        if licence_key:
            return licence_key
        else:
            print("Invalid input. Please, try again.")


def main() -> None:
    initial_message = """


StackAI Environment Variable Initialization script.

This script will initialize the environment variables needed to run the StackAI services with
sensible default values.

Inside each folder (stackend, mongodb, ...) there is a `.env` file containing the environment variables
needed to run the service. For instance, the `stackend/.env` file contains the environment variables needed
to run the StackAI stackend service.

Please, feel free to edit the generated files to better suit your needs.
    """

    root_project_path = Path(__file__).absolute().parent.parent.parent

    weaviate_template = environment.get_template("weaviate.env.template")
    mongodb_template = environment.get_template("mongodb.env.template")
    unstructured_template = environment.get_template("unstructured.env.template")
    stackrepl_template = environment.get_template("stackrepl.env.template")
    supabase_template = environment.get_template("supabase.env.template")
    stackend_template = environment.get_template("stackend.env.template")
    stackweb_template = environment.get_template("stackweb.env.template")

    print(initial_message)

    print("""
============================================================
FIRST STEP: PLEASE INPUT THE FOLLOWING VALUES MANUALLY
============================================================
""")

    virtual_machine_ip_or_domain = get_virtual_machine_ip_or_domain()
    licence_key = get_licence_key()
    print(f"""
The following variables will be used to fill in the templates:

- VIRTUAL_MACHINE_IP_OR_URL: {virtual_machine_ip_or_domain}
- STACKAI_LICENCE: {licence_key}
""")

    input("Press enter to confirm, use Control+C to abort :")

    # Fill in weaviate template and save it.
    weaviate_template_variables = get_weaviate_template_variables()
    weaviate_folder = root_project_path / "weaviate"
    print(f"\n~> Filling in weaviate template and saving it to {weaviate_folder}")
    render_and_save_template(
        weaviate_template,
        weaviate_template_variables,
        weaviate_folder,
        ".env",
    )
    print(
        f"~> The weaviate .env file has been filled in and saved to {weaviate_folder}.env"
    )

    # Fill in mongodb template and save it.
    mongodb_template_variables = get_mongodb_template_variables()
    mongodb_folder = root_project_path / "mongodb"
    print(f"\n~> Filling in mongodb template and saving it to {mongodb_folder}")
    render_and_save_template(
        mongodb_template,
        mongodb_template_variables,
        mongodb_folder,
        ".env",
    )
    print(
        f"~> The mongodb .env file has been filled in and saved to {mongodb_folder}.env"
    )

    # Fill in unstructured io template and save it.
    unstructured_template_variables = get_unstructured_template_variables()
    unstructured_folder = root_project_path / "unstructured"
    print(
        f"\n~> Filling in unstructured io template and saving it to {unstructured_folder}"
    )
    render_and_save_template(
        unstructured_template,
        unstructured_template_variables,
        unstructured_folder,
        ".env",
    )
    print(
        f"~> The unstructured .env file has been filled in and saved to {unstructured_folder}.env"
    )

    # Fill in stackrepl template and save it.
    stackrepl_template_variables = get_stackrepl_template_variables()
    stackrepl_folder = root_project_path / "stackrepl"
    print(f"\n~> Filling in stackrepl template and saving it to {stackrepl_folder}")
    render_and_save_template(
        stackrepl_template,
        stackrepl_template_variables,
        stackrepl_folder,
        ".env",
    )
    print(
        f"~> The stackrepl .env file has been filled in and saved to {stackrepl_folder}.env"
    )

    # Fill in supabase template and save it.
    supabase_template_variables = get_supabase_template_variables(
        virtual_machine_ip_or_url=virtual_machine_ip_or_domain,
    )
    supabase_folder = root_project_path / "supabase"
    print(f"\n~> Filling in supabase template and saving it to {supabase_folder}")
    render_and_save_template(
        supabase_template,
        supabase_template_variables,
        supabase_folder,
        ".env",
    )
    print(
        f"~> The supabase .env file has been filled in and saved to {supabase_folder}.env"
    )

    # Fill in stackend template and save it.
    mongodb_uri = f"mongodb://{mongodb_template_variables['MONGODB_ROOT_USERNAME']}:{mongodb_template_variables['MONGODB_ROOT_PASSWORD']}@mongodb:27017"

    stackend_template_variables = get_stackend_template_variables(
        mongodb_uri=mongodb_uri,
        supabase_anon_key=supabase_template_variables["ANON_KEY"],
        supabase_service_role_key=supabase_template_variables["SERVICE_ROLE_KEY"],
        postgres_password=supabase_template_variables["POSTGRES_PASSWORD"],
        unstructured_api_key=unstructured_template_variables["UNSTRUCTURED_API_KEY"],
        weaviate_api_key=weaviate_template_variables["WEAVIATE_API_KEY"],
        virtual_machine_ip_or_url=virtual_machine_ip_or_domain,
        stackai_licence=licence_key,
        minio_password=supabase_template_variables["MINIO_PASSWORD"],
    )
    stackend_folder = root_project_path / "stackend"
    print(f"\n~> Filling in stackend template and saving it to {stackend_folder}")
    render_and_save_template(
        stackend_template,
        stackend_template_variables,
        stackend_folder,
        ".env",
    )
    print(
        f"~> The stackend .env file has been filled in and saved to {stackend_folder}.env"
    )

    # Fill in stackweb template and save it.
    stackweb_template_variables = get_stackweb_template_variables(
        virtual_machine_ip_or_url=virtual_machine_ip_or_domain,
        supabase_anon_key=supabase_template_variables["ANON_KEY"],
        supabase_service_role_key=supabase_template_variables["SERVICE_ROLE_KEY"],
    )
    stackweb_folder = root_project_path / "stackweb"
    print(f"\n~> Filling in stackweb template and saving it to {stackweb_folder}")
    render_and_save_template(
        stackweb_template,
        stackweb_template_variables,
        stackweb_folder,
        ".env",
    )
    print(
        f"~> The stackweb .env file has been filled in and saved to {stackweb_folder}.env"
    )


if __name__ == "__main__":
    main()
