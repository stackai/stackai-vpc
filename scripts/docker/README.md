# StackAI Version Management

This directory contains tools for managing StackAI service versions across the on-premise deployment.

## Files

- `stackai-versions.json` - Configuration file containing version mappings
- `update_stackai_versions.py` - Python script that updates service versions
- `README.md` - This documentation file

## Configuration Format

The `stackai-versions.json` file contains an array of version objects. Each object maps a release version to specific service versions:

```json
[
  {
    "1.0.2": {
      "stackend": "v1.0.2",
      "stackweb": "v1.0.3",
      "stackrepl": "v1.0.0"
    }
  }
]
```

## Usage

### Using Make (Recommended)

```bash
# Update to a specific version
make stackai-version version=1.0.2

# Show help
make stackai-version
```

### Using Python Script Directly

```bash
# Update to a specific version
python3 scripts/docker/update_stackai_versions.py 1.0.2

# Show help
python3 scripts/docker/update_stackai_versions.py
```

## What Gets Updated

The script updates the following files:

1. **stackend/docker-compose.yml**

   - `stackai.azurecr.io/stackai/stackend-celery-worker:VERSION`
   - `stackai.azurecr.io/stackai/stackend-backend:VERSION`

2. **stackweb/Dockerfile**

   - `FROM stackai.azurecr.io/stackai/stackweb:VERSION`

3. **stackrepl/docker-compose.yml**
   - `stackai.azurecr.io/stackai/stackrepl/stack-repl:VERSION`

## Adding New Versions

To add a new version configuration:

1. Edit `scripts/docker/stackai-versions.json`
2. Add a new object with the version and service mappings:

```json
{
  "1.0.3": {
    "stackend": "v1.0.3",
    "stackweb": "v1.0.4",
    "stackrepl": "v1.0.1"
  }
}
```

## After Updating Versions

After running the version update script, you should:

1. **Review changes**: `git diff`
2. **Update services**: `make update` (pulls new images and restarts services)
3. **Commit changes**: `git add . && git commit -m "Update to version X.X.X"`

## Example Workflow

```bash
# 1. Update to new version
make stackai-version version=1.0.2

# 2. Review the changes
git diff

# 3. Update and restart services
make update

# 4. Commit the changes
git add .
git commit -m "Update StackAI services to version 1.0.2"
```
