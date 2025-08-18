echo "This script will set up a user in supabase for test logins"
echo "First we do a git pull"
git pull

EMAIL='user00@stack-ai.com'
PASSWORD='pw123'

# Update Load Balancer IP in helmrelease.yaml
echo "Updating Load Balancer IP in helmrelease.yaml..."
echo "New Load Balancer IP: $ING_IP"


REPO_BASE="$(git rev-parse --show-toplevel)"
APIKEY=$(cat ${REPO_BASE}/components/helmreleases/supabase/24.03.03/aks/secrets.yaml| yq '.stringData.serviceKey' | head -n1)
ING_IP=$(kubectl get ing -n flux-system | grep supabase | awk '{print $4}')

# Update all occurrences of IP addresses in URLs with the new ING_IP
# This will match patterns like http://X.X.X.X:8000 and replace the IP part
sed -i '' "s|http://[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}|http://$ING_IP|g" ${REPO_BASE}/components/helmreleases/supabase/24.03.03/base/helmrelease.yaml
sed -i '' "s|http://[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}|http://$ING_IP|g" ${REPO_BASE}/components/kustomizations/stackweb/VERSION/base/stackweb--env-configmap.yaml
echo "Updated helmrelease.yaml with new Ingress IP: $ING_IP"
git diff ${REPO_BASE}/components/helmreleases/supabase/24.03.03/base/helmrelease.yaml
git diff ${REPO_BASE}/components/kustomizations/stackweb/VERSION/base/stackweb--env-configmap.yaml

# Check if we're not on main branch and commit the changes
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Committing changes to branch: $CURRENT_BRANCH"
    git add ${REPO_BASE}/components/helmreleases/supabase/24.03.03/base/helmrelease.yaml
    git add ${REPO_BASE}/components/kustomizations/configuration-setup/VERSION/base/stackweb--env-configmap.yaml
    git commit -m "AUTOMATED: Set Ingress IP to $ING_IP for supabase and stackweb"
    git push
    
    echo "Triggering flux reconciliation..."
    flux reconcile ks -n flux-system flux-system --with-source
    flux reconcile ks -n flux-system crds
    flux reconcile ks -n flux-system system
    flux reconcile ks -n flux-system stackend
    flux reconcile ks -n flux-system stackweb
    echo "Flux reconciliation triggered"
else
    echo "On main branch - skipping automatic commit"
    echo "You can now commit this change to git"
fi


# Create user and capture response
echo "Setting up port-forward to Kong..."
kubectl port-forward -n flux-system svc/supabase-supabase-kong 8000:8000 &
PF_PID=$!
echo $PF_PID
sleep 5  # Give port-forward time to establish

RESPONSE=$(curl -X POST http://localhost:8000/auth/v1/admin/users \
  -H "Authorization: Bearer $APIKEY" \
  -H "Content-Type: application/json" \
  -H "apikey: $APIKEY" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"email_confirm\":true}")
echo "User creation response: $RESPONSE"

# Stop Kong Port-Forward
echo "Stopping Kong Port-Forward..."
kill $PF_PID
echo "Port-forward closed"
unset PF_PID

# Extract user_id from response
USER_ID=$(echo $RESPONSE | jq -r '.id')
echo "Created user with ID: $USER_ID"

# Setup port-forward to PostgreSQL
echo "Setting up port-forward to PostgreSQL..."
kubectl port-forward -n flux-system svc/supabase-supabase-db 5432:5432 &
PF_PID=$!
sleep 5  # Give port-forward time to establish

# Get PostgreSQL password
POSTGRES_PASSWORD=$(cat ${REPO_BASE}/components/helmreleases/supabase/24.03.03/aks/secrets.yaml | yq '.stringData.password' | head -n1)
export PGPASSWORD=$POSTGRES_PASSWORD

# Generate a random organization ID
ORG_ID=$(openssl rand -hex 16)
echo "Generated organization ID: $ORG_ID"

# Execute database operations
echo "Creating database entries..."

# 1. Add user to profiles table
psql -h localhost -p 5432 -U postgres -d postgres -c "INSERT INTO profiles (id, email) VALUES ('$USER_ID', '$EMAIL');"
echo "Added user to profiles table"

# 2. Create organization
psql -h localhost -p 5432 -U postgres -d postgres -c "INSERT INTO organizations (org_id) VALUES ('$ORG_ID');"
echo "Created organization"

# 3. Look up admin role_id from roles table
ADMIN_ROLE_ID=$(psql -h localhost -p 5432 -U postgres -d postgres -t -c "SELECT id FROM roles WHERE name = 'admin';" | xargs)
echo "Admin role ID: $ADMIN_ROLE_ID"

# 4. Associate user with organization as admin
psql -h localhost -p 5432 -U postgres -d postgres -c "INSERT INTO user_organizations (user_id, org_id, role_id) VALUES ('$USER_ID', '$ORG_ID', '$ADMIN_ROLE_ID');"
echo "Associated user with organization as admin"

# Cleanup
echo "Cleaning up..."
kill $PF_PID
echo "Port-forward closed"

echo "User setup complete!"
echo "Email: $EMAIL"
echo "User ID: $USER_ID"
echo "Organization ID: $ORG_ID"

echo "restarting stackweb and kong pods to complete setup"
kubectl delete pod -n flux-system $(kubectl get pod -n flux-system | grep kong | awk '{print $1}')
kubectl delete pod -n flux-system $(kubectl get pod -n flux-system | grep stackweb | awk '{print $1}')

echo "=============="
echo "setup complete"
