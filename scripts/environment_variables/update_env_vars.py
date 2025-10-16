# TODO: script to update or create environment variables:
#
# We need to update/create env vars in the following paths:
# - stackend/.env
# - stackweb/.env
# - supabase/.env
# - weaviate/.env
# - mongodb/.env
# - unstructured/.env
# - stackrepl/.env


from dataclasses import dataclass
import pathlib

# Get the workspace root (2 levels up from this script)
SCRIPT_DIR = pathlib.Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent


paths = {
    "stackend": WORKSPACE_ROOT / "stackend" / ".env",
}

# named tuple to represent an environment variable
@dataclass
class EnvVar:
    """An environment variable."""
    key: str
    value: str | bool

@dataclass
class EnvReference:
    """Create or update an environment variable with an existing variable value."""
    key: str
    reference_key: str

stackend_variables = [
    EnvVar(key="ON_PREMISE", value="fonsi"),
    EnvReference(key="ON_PREMISE", reference_key="COHERE_API_KEY"),
]

variables = {
    "stackend": stackend_variables,
}

def _update_env_file_variable(content: str, variable: EnvVar | EnvReference) -> str:
    """Update an environment variable in a .env file."""
    lines = content.splitlines(keepends=True)
    
    match variable:
        case EnvVar():
            # Update or create the variable
            key_found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{variable.key}="):
                    # Replace this line
                    lines[i] = f"{variable.key}={variable.value}\n"
                    key_found = True
                    break
            
            if not key_found:
                # Add the variable at the end
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                lines.append(f"{variable.key}={variable.value}\n")
            
        case EnvReference():
            # Find the reference variable
            reference_value = None
            for line in lines:
                if line.startswith(f"{variable.reference_key}="):
                    reference_value = line.split('=', 1)[1].strip()
                    break
            
            if reference_value is None:
                raise ValueError(f"Variable {variable.reference_key} not found in content.")
            
            # Now update or create the key with the reference value
            key_found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{variable.key}="):
                    lines[i] = f"{variable.key}={reference_value}\n"
                    key_found = True
                    break
            
            if not key_found:
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                lines.append(f"{variable.key}={reference_value}\n")
            
    return ''.join(lines)


def update_env_file_variables(path: pathlib.Path, variables: list[EnvVar | EnvReference]) -> None:
    """Update or create environment variables in a .env file."""
    if not path.is_file():
        raise FileNotFoundError(f"File {path} does not exist.")

    with open(path, "r") as f:
        content = f.read()

    for variable in variables:
        content = _update_env_file_variable(content, variable)

    with open(path, "w") as f:
        f.write(content)

def main() -> None:
    print("Updating environment variables...")
    for key, path in paths.items():
        variables_list = variables[key]
        print(f"Updating {key} with {path}")
        update_env_file_variables(path, variables_list)
    print("Environment variables updated successfully.")

if __name__ == "__main__":
    main()