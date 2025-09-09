#!/bin/bash
set -euo pipefail

# Ensure no command echoing
set +x

# Validate environment
if [ -z "${SOPS_AGE_KEY_FILE:-}" ]; then
  echo "ERROR: SOPS_AGE_KEY_FILE not set" >&2
  exit 1
fi

# Apply the secret silently
if sops --decrypt ../../sops/clusters/aks/sops-age-key-secret.enc.yaml 2>/dev/null | \
   kubectl apply -n flux-system -f - >/dev/null 2>&1; then
  echo "SOPS secret applied successfully"
else
  echo "ERROR: Failed to apply SOPS secret" >&2
  exit 1
fi