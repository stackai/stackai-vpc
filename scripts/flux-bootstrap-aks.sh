#!/bin/bash
set -e

# Configuration
GITHUB_ORG="stackai"
GITHUB_REPO="stackai-onprem"
BRANCH="on-prem-aks"
CLUSTER_PATH="./clusters/aks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl is required but not installed.${NC}"; exit 1; }
command -v flux >/dev/null 2>&1 || { echo -e "${RED}flux CLI is required but not installed.${NC}"; exit 1; }

# Verify cluster connection
echo "Verifying cluster connection..."
kubectl cluster-info || { echo -e "${RED}Cannot connect to Kubernetes cluster${NC}"; exit 1; }

# Check if flux-system namespace exists
if kubectl get namespace flux-system &> /dev/null; then
    echo -e "${YELLOW}flux-system namespace already exists. Checking if Flux is installed...${NC}"
    if flux check --pre &> /dev/null; then
        echo -e "${YELLOW}Flux appears to be already installed. Proceed with caution.${NC}"
        read -p "Do you want to continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "Creating flux-system namespace..."
    kubectl create namespace flux-system
fi

# Install Flux CRDs first
echo "Installing Flux CRDs..."
flux install \
  --namespace=flux-system \
  --network-policy=false \
  --components-extra=image-reflector-controller,image-automation-controller \
  --export | kubectl apply -f -

# Wait for CRDs to be established
echo "Waiting for CRDs to be established..."
kubectl wait --for condition=established --timeout=60s crd/gitrepositories.source.toolkit.fluxcd.io
kubectl wait --for condition=established --timeout=60s crd/kustomizations.kustomize.toolkit.fluxcd.io

# No authentication needed for public repository
echo "Using public repository - no authentication required"

# Apply the GitRepository and root Kustomization
echo "Applying GitRepository and Kustomization..."
flux create source git flux-system \
  --url="https://github.com/${GITHUB_ORG}/${GITHUB_REPO}" \
  --branch="${BRANCH}" \
  --interval=1m \
  --export | kubectl apply -f -

flux create kustomization flux-system \
  --source=GitRepository/flux-system \
  --path="${CLUSTER_PATH}" \
  --prune=true \
  --interval=10m \
  --export | kubectl apply -f -

# No cleanup needed for public repository

echo -e "${GREEN}Bootstrap completed!${NC}"
echo "Checking Flux components..."
flux check

echo ""
echo "Watching reconciliation..."
echo "Press Ctrl+C to exit"
flux get kustomizations --watch