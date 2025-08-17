#!/bin/bash
set -e

# Default values
GITHUB_OWNER="stackai"
REPO_NAME="stackai-onprem"
BRANCH="on-prem-aks-auto-flux-bootstrap"
REPO_BASE="$(git rev-parse --show-toplevel)"
FLUX_PATH="./clusters/aks"




# Help message
usage() {
    echo "Usage: $0 [-o github_owner] [-r repo_name] [-b branch] [-p path]"
    echo
    echo "Bootstrap Flux on a Kubernetes cluster"
    echo
    echo "Options:"
    echo "  -o    GitHub owner/organization (default: $GITHUB_OWNER)"
    echo "  -r    Repository name (default: $REPO_NAME)"
    echo "  -b    Branch name (default: $BRANCH)"
    echo "  -p    FLUX_PATH (default: $FLUX_PATH)"
    echo "  -h    Show this help message"
    exit 1
}

# Parse command line arguments
while getopts "o:r:b:p:h" opt; do
    case $opt in
        o) GITHUB_OWNER="$OPTARG" ;;
        r) REPO_NAME="$OPTARG" ;;
        b) BRANCH="$OPTARG" ;;
        p) FLUX_PATH="$OPTARG" ;;
        h) usage ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
    esac
done

CLUSTER_PATH="${REPO_BASE}/${FLUX_PATH}"

# Get the current Git branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Compare
if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
    echo "Current branch '$CURRENT_BRANCH' is NOT '$BRANCH'"
    # You can add actions here, for example:
    # exit 1
else
    echo "On target branch '$BRANCH'"
fi

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token is required. Either set GITHUB_TOKEN environment variable or use -t flag."
    echo 'Error: Example "export GITHUB_TOKEN=$(gh auth token)"'
    exit 1
fi

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "Error: kubectl is not configured or cluster is not accessible"
    exit 1
fi

echo "🔄 Checking Flux CLI installation..."
if ! command -v flux &>/dev/null; then
    echo "⚠️  Flux CLI not found. Installing..."
    brew install fluxcd/tap/flux
fi

echo "🏗️  Checking cluster directory: $FLUX_PATH"
if [ ! -d "$CLUSTER_PATH" ]; then
    echo "Error: Directory $FLUX_PATH does not exist"
    echo "Please ensure the cluster directory exists before running this script"
    exit 1
fi

echo "🧹 Cleaning up any existing Flux installation..."
# Only try to clean up if Flux CRDs exist
if kubectl get crd kustomizations.kustomize.toolkit.fluxcd.io &>/dev/null; then
    kubectl delete kustomization flux-system -n flux-system --ignore-not-found=true || true
fi
flux uninstall --keep-namespace --silent || true

echo "🚀 Bootstrapping Flux at path: $FLUX_PATH..."
flux bootstrap github \
    --owner="$GITHUB_OWNER" \
    --repository="$REPO_NAME" \
    --branch="$BRANCH" \
    --path="$FLUX_PATH" \
    --personal \
    --token-auth \
    --components-extra=image-reflector-controller,image-automation-controller

echo "⏳ Waiting for Flux controllers to be ready..."
kubectl -n flux-system wait --for=condition=ready pod --all --timeout=2m

echo "✅ Flux bootstrap completed successfully at path: $FLUX_PATH!"
echo "📊 Checking Flux system health..."
flux check

echo "🔍 Current Flux resources:"
flux get all -A
