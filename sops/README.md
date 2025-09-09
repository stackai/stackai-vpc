# SOPS Encryption Setup

This directory contains encrypted secrets and cluster keys for the Stack AI on-premises deployment.

## Key Hierarchy

1. **Master Key** (`export SOPS_AGE_KEY_FILE='/path/to/key'`)
   - Top-level key with ultimate access
   - Stored locally, never committed to Git
   - Can decrypt everything including the GitHub repo key

2. **GitHub Repo Key** (`sops/github-secret.age.enc`)
   - Repository master key for CI/CD operations
   - Encrypted with the master key
   - Used as GitHub Actions secret
   - Can decrypt all cluster keys and secrets in the repo

3. **Cluster Keys** (e.g., `sops/clusters/aks/sops-age-key-secret.enc.yaml`)
   - Cluster-specific keys for Flux decryption
   - Encrypted with both master and GitHub repo keys
   - Applied directly to clusters, not managed by Flux

## Directory Structure

```
sops/
├── .gitignore                    # Excludes unencrypted files
├── README.md                     # This file
├── github-secret.age.enc         # Encrypted GitHub repo key
└── clusters/
    └── aks/
        └── sops-age-key-secret.enc.yaml  # Encrypted K8s secret with cluster key
```

## Usage

### Decrypting with Master Key

`ensure SOPS_AGE_KEY_FILE is set`

```bash
sops --decrypt sops/clusters/aks/sops-age-key-secret.enc.yaml
```

### Applying Cluster Key to Kubernetes
```bash
# First decrypt the secret
sops --decrypt sops/clusters/aks/sops-age-key-secret.enc.yaml | kubectl apply -f -
```

## SOPS Configuration

The `.sops.yaml` file in the repository root defines encryption rules:
- Files in `sops/clusters/` are encrypted with master + GitHub keys
- Files in `clusters/` and `components/` are encrypted with master + GitHub + cluster keys
- This ensures proper access control at each level
