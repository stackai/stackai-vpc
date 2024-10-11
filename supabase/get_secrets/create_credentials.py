import secrets
import string
import time

import jwt


def generate_password(length=32):
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt(role, secret):
    iat = int(time.time())
    exp = iat + (5 * 365 * 24 * 60 * 60)  # 5 years from now
    payload = {"role": role, "iss": "supabase", "iat": iat, "exp": exp}
    return jwt.encode(payload, secret, algorithm="HS256")


# Generate PostgreSQL password
psql_password = generate_password()

# Generate JWT secret
jwt_secret = generate_password(40)

# Generate anon and service role keys
anon_key = generate_jwt("anon", jwt_secret)
service_role_key = generate_jwt("service_role", jwt_secret)

# Generate a password for the supabase dashboard
dashboard_password = generate_password(length=16)

# Generate Logflare keys
logflare_logger_backend_api_key = generate_password()
logflare_api_key = generate_password()

# Print the generated credentials
print("\n" * 5)
print("=" * 80)
print("Generating credentials...")

# Optionally, you can write these to a .env file
with open(".env", "w") as env_file:
    env_file.write("# Database\n")
    env_file.write(f"POSTGRES_PASSWORD={psql_password}\n")
    env_file.write("\n")
    env_file.write("# Kong ANON/SERVICE ROLE KEYS\n")
    env_file.write(f"JWT_SECRET={jwt_secret}\n")
    env_file.write(f"ANON_KEY={anon_key}\n")
    env_file.write(f"SERVICE_ROLE_KEY={service_role_key}\n")
    env_file.write("\n")
    env_file.write("# Supabase Studio Dashboard\n")
    env_file.write("DASHBOARD_USERNAME=stack_supabase\n")
    env_file.write(f"DASHBOARD_PASSWORD={dashboard_password}\n")
    env_file.write("\n")
    env_file.write("# Logflare\n")
    env_file.write(
        f"LOGFLARE_LOGGER_BACKEND_API_KEY={logflare_logger_backend_api_key}\n"
    )
    env_file.write(f"LOGFLARE_API_KEY={logflare_api_key}\n")

print("Credentials have been written to .env file in the get_secrets directory")
print("SUCCESS!!")
print("=" * 80)
