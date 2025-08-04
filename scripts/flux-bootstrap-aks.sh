#!/bin/bash
set -e

# Default values
GITHUB_OWNER="stackai"
REPO_NAME="stackai-onprem"
BRANCH="on-prem-aks"
ACCOUNT_NAME=""
CLUSTER_NAME=""
CLUSTER_PATH="./clusters/aks"

# Help message
usage() {
    echo "Usage: $0 -a account_name -c cluster_name [-t github_token] [-o github_owner] [-r repo_name] [-b branch] [-m]"
    echo
    echo "Bootstrap Flux on a Kubernetes cluster"
    echo
    echo "Required Options:"
    echo "  -a    Account name (e.g., 'management', 'dev-account', 'prod-account')"
    echo "  -c    Cluster name (e.g., 'primary', 'dev-cluster')"
    echo
    echo "Options:"
    echo "  -m    Bootstrap as management cluster (includes Crossplane & Cluster API)"
    echo "  -t    GitHub personal access token (required if GITHUB_TOKEN env var is not set)"
    echo "  -o    GitHub owner/organization (default: $GITHUB_OWNER)"
    echo "  -r    Repository name (default: $REPO_NAME)"
    echo "  -b    Branch name (default: $BRANCH)"
    echo "  -h    Show this help message"
    exit 1
}

# Parse command line arguments
while getopts "a:c:t:o:r:b:mh" opt; do
    case $opt in
        a) ACCOUNT_NAME="$OPTARG" ;;
        c) CLUSTER_NAME="$OPTARG" ;;
        t) GITHUB_TOKEN="$OPTARG" ;;
        o) GITHUB_OWNER="$OPTARG" ;;
        r) REPO_NAME="$OPTARG" ;;
        b) BRANCH="$OPTARG" ;;
        m) CLUSTER_TYPE="management" ;;
        h) usage ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
    esac
done

# Check required arguments
if [ -z "$ACCOUNT_NAME" ]; then
    echo "Error: Account name is required (-a flag)"
    usage
fi

if [ -z "$CLUSTER_NAME" ]; then
    echo "Error: Cluster name is required (-c flag)"
    usage
fi

# Set Flux path based on account and cluster
FLUX_PATH="clusters/$ACCOUNT_NAME/$CLUSTER_NAME"

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

echo "🏗️  Setting up cluster directory structure..."
if [ ! -d "$FLUX_PATH" ]; then
    echo "   Creating cluster directory: $FLUX_PATH"
    mkdir -p "$FLUX_PATH"
    
    # Create account-level kustomization if it doesn't exist
    ACCOUNT_PATH="clusters/$ACCOUNT_NAME"
    if [ ! -f "$ACCOUNT_PATH/kustomization.yaml" ]; then
        echo "   Creating account kustomization for $ACCOUNT_NAME"
        cat > "$ACCOUNT_PATH/kustomization.yaml" <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: aws-$ACCOUNT_NAME

resources:
  # Clusters will be added here
  - $CLUSTER_NAME
EOF
    else
        # Add cluster to existing account kustomization if not already present
        if ! grep -q "  - $CLUSTER_NAME" "$ACCOUNT_PATH/kustomization.yaml"; then
            echo "   Adding $CLUSTER_NAME to account kustomization"
            sed -i.bak "/resources:/a\\  - $CLUSTER_NAME" "$ACCOUNT_PATH/kustomization.yaml"
            rm "$ACCOUNT_PATH/kustomization.yaml.bak"
        fi
    fi
    
    # Always start with system template as base
    echo "   Setting up base system components from template..."
    cp -r clusters/_template/system/* "$FLUX_PATH/"
    
    # Replace placeholders in all yaml files
    echo "   Updating paths with account and cluster names..."
    find "$FLUX_PATH" -name "*.yaml" -type f -exec sed -i.bak \
        -e "s|ACCOUNT_NAME|$ACCOUNT_NAME|g" \
        -e "s|CLUSTER_NAME|$CLUSTER_NAME|g" {} \;
    # Remove backup files
    find "$FLUX_PATH" -name "*.yaml.bak" -type f -delete
    
    if [ "$CLUSTER_TYPE" = "management" ]; then
        echo "   Adding management cluster components..."
        # Copy management-specific components (crossplane and cluster-api)
        cp -r clusters/_template/management/crossplane* "$FLUX_PATH/"
        cp -r clusters/_template/management/cluster-api* "$FLUX_PATH/"
        
        # Replace placeholders in the newly copied management files
        find "$FLUX_PATH" -name "*.yaml" -type f -exec sed -i.bak \
            -e "s|ACCOUNT_NAME|$ACCOUNT_NAME|g" \
            -e "s|CLUSTER_NAME|$CLUSTER_NAME|g" {} \;
        # Remove backup files
        find "$FLUX_PATH" -name "*.yaml.bak" -type f -delete
        
        # Add management components to kustomization.yaml using yq
        if ! command -v yq &>/dev/null; then
            echo "Error: yq is required for management clusters but not found in PATH"
            echo "Please install yq: brew install yq"
            exit 1
        fi
        yq eval -i '.resources += ["crossplane.yaml", "cluster-api.yaml"]' "$FLUX_PATH/kustomization.yaml"
    fi
    
    echo "   Committing cluster configuration..."
    git add "clusters/$ACCOUNT_NAME"
    git commit -m "Add $CLUSTER_TYPE cluster configuration for $ACCOUNT_NAME/$CLUSTER_NAME"
    git push origin "$BRANCH"
fi

echo "🧹 Cleaning up any existing Flux installation..."
# Delete the flux-system kustomization if it exists to avoid path conflicts
kubectl delete kustomization flux-system -n flux-system --ignore-not-found=true || true
flux uninstall --keep-namespace --silent || true

echo "🚀 Bootstrapping Flux for $CLUSTER_TYPE cluster: $ACCOUNT_NAME/$CLUSTER_NAME..."
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

echo "✅ Flux bootstrap completed successfully for $CLUSTER_TYPE cluster: $ACCOUNT_NAME/$CLUSTER_NAME!"
echo "📊 Checking Flux system health..."
flux check

echo "🔍 Current Flux resources:"
flux get all -A
