#!/bin/bash
set -euo pipefail

# Check SOPS_AGE_KEY_FILE
if [ -z "${SOPS_AGE_KEY_FILE:-}" ]; then
  echo "ERROR: SOPS_AGE_KEY_FILE environment variable is not set" >&2
  echo "Please set: export SOPS_AGE_KEY_FILE=/path/to/your/key" >&2
  exit 1
fi

if [ ! -f "$SOPS_AGE_KEY_FILE" ]; then
  echo "ERROR: SOPS_AGE_KEY_FILE points to non-existent file: $SOPS_AGE_KEY_FILE" >&2
  exit 1
fi

if [ ! -r "$SOPS_AGE_KEY_FILE" ]; then
  echo "ERROR: SOPS_AGE_KEY_FILE is not readable: $SOPS_AGE_KEY_FILE" >&2
  exit 1
fi

# Check GITHUB_TOKEN
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: GITHUB_TOKEN environment variable is not set" >&2
  echo "Please set: export GITHUB_TOKEN=\$(gh auth token)" >&2
  exit 1
fi

# Validate GITHUB_TOKEN is not empty
if [ "$GITHUB_TOKEN" = "" ]; then
  echo "ERROR: GITHUB_TOKEN is empty" >&2
  echo "Please authenticate with GitHub CLI: gh auth login" >&2
  exit 1
fi

echo '{"validated": "true"}'