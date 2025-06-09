# 🚀 StackAI Post-Deployment Steps

After your CDK infrastructure deployment completes, you need to follow these steps to get your StackAI application running.

## ✅ Prerequisites

1. CDK deployment completed successfully (`CREATE_COMPLETE` status)
2. Docker installed and running on your machine
3. kubectl installed
4. AWS CLI configured with appropriate permissions

## 📋 Step-by-Step Deployment

### 1. Check Infrastructure Status

```bash
# Check if CDK deployment completed
export AWS_DEFAULT_REGION=us-east-2
python3 -c "import boto3; cf = boto3.client('cloudformation', region_name='us-east-2'); print(cf.describe_stacks(StackName='StackaiEksCdkStack')['Stacks'][0]['StackStatus'])"
```

Wait until status shows `CREATE_COMPLETE` before proceeding.

### 2. Get Connection Information

```bash
# Run the helper script to get all connection details
./get-connection-info.sh
```

This will output:

- EKS cluster name
- Aurora database endpoint
- DocumentDB endpoint
- Redis endpoint
- S3 bucket name
- Connection strings for your applications

### 3. Configure kubectl

```bash
# Configure kubectl to connect to your EKS cluster
aws eks update-kubeconfig --region us-east-2 --name [CLUSTER_NAME_FROM_STEP_2]

# Verify connection
kubectl get nodes
kubectl get pods -A
```

### 4. Build and Push Docker Images

```bash
# Build Docker images for your application services
./build-images.sh
```

This script will:

- Create ECR repositories
- Build Docker images for StackWeb, StackEnd, and StackRepl
- Push images to ECR

### 5. Update Configuration

Edit `deploy-applications.sh` and update the following:

1. **CLUSTER_NAME**: Use the name from step 2
2. **Database connection strings**: Replace placeholders with actual endpoints
3. **Docker image URIs**: Use the ECR URIs from step 4
4. **API keys and secrets**: Replace placeholder values

Example updates needed:

```bash
# Update in deploy-applications.sh
CLUSTER_NAME="your-actual-cluster-name"

# Replace placeholder connection strings
- value: "postgresql://postgres:PASSWORD@AURORA_ENDPOINT:5432/postgres"
+ value: "postgresql://postgres:YOUR_ACTUAL_PASSWORD@your-aurora-endpoint.amazonaws.com:5432/postgres"

# Replace placeholder image URIs
- image: stackai/stackweb:latest
+ image: 881490119564.dkr.ecr.us-east-2.amazonaws.com/stackai/stackweb:latest
```

### 6. Get Database Passwords

```bash
# Get Aurora password from Secrets Manager
aws secretsmanager get-secret-value --secret-id StackaiEksCdkStack-ManagedServices-AuroraSecret --region us-east-2 --query SecretString --output text | jq -r .password

# Get DocumentDB password from Secrets Manager
aws secretsmanager get-secret-value --secret-id StackaiEksCdkStack-ManagedServices-DocDbSecret --region us-east-2 --query SecretString --output text | jq -r .password
```

### 7. Deploy Applications

```bash
# Deploy all application services to EKS
./deploy-applications.sh
```

This will deploy:

- StackWeb (frontend)
- StackEnd (backend + Celery workers)
- StackRepl (code execution)
- Weaviate (vector database)
- Unstructured API (document processing)
- Ingress for external access

### 8. Verify Deployment

```bash
# Check if all pods are running
kubectl get pods -A

# Check ingress and load balancer status
kubectl get ingress -A
kubectl get svc -A | grep LoadBalancer

# Get load balancer URL
kubectl get ingress stackai-main-ingress -n stackweb -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 9. Database Initialization

**Supabase Database Setup:**

```bash
# Connect to Aurora and run Supabase migrations
kubectl exec -it deployment/gotrue -n supabase -- /bin/sh

# Inside the container, run database migrations
# (Supabase will automatically create required tables on first startup)
```

**StackEnd Database Setup:**

```bash
# Connect to StackEnd backend pod
kubectl exec -it deployment/stackend-backend -n stackend -- /bin/sh

# Run database migrations
python manage.py migrate  # If using Django
# or
alembic upgrade head      # If using SQLAlchemy/Alembic
```

### 10. Configure DNS and SSL

1. **Get Load Balancer URL:**

   ```bash
   kubectl get ingress stackai-main-ingress -n stackweb -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
   ```

2. **Set up DNS records:**

   - Point `app.stackai.com` to the load balancer
   - Point `api.stackai.com` to the load balancer
   - Point `backend.stackai.com` to the load balancer

3. **Configure SSL certificates:**

   ```bash
   # Install cert-manager for automatic SSL
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

   # Create certificate issuer (Let's Encrypt)
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: your-email@domain.com
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
       - http01:
           ingress:
             class: alb
   EOF
   ```

## 🔧 Configuration Files You May Need to Update

### Environment Variables

- **StackWeb**: Frontend configuration in deployment manifest
- **StackEnd**: Backend API and database connections
- **Supabase**: JWT secrets, API keys, SMTP settings

### API Keys and Secrets

- Supabase JWT secret
- Supabase anon and service role keys
- Weaviate API key
- Unstructured API key
- SMTP credentials for email

### Domain Configuration

- Update all domain references to your actual domains
- Configure CORS settings for your domains

## 📊 Monitoring and Troubleshooting

### Check Application Status

```bash
# View all pods
kubectl get pods -A

# Check specific service logs
kubectl logs -f deployment/stackweb -n stackweb
kubectl logs -f deployment/stackend-backend -n stackend
kubectl logs -f deployment/gotrue -n supabase

# Check ingress status
kubectl describe ingress stackai-main-ingress -n stackweb
```

### Common Issues

1. **Pods stuck in Pending**: Check node capacity and resource requests
2. **ImagePullBackOff**: Verify ECR image URIs and IAM permissions
3. **Database connection errors**: Check security groups and connection strings
4. **Load balancer not provisioning**: Check ALB controller logs

### Health Checks

Once everything is deployed, test these endpoints:

- `http://[LOAD_BALANCER_URL]/` - StackWeb frontend
- `http://[LOAD_BALANCER_URL]/health` - Supabase health check
- `http://backend.[DOMAIN]/health` - StackEnd health check

## 🎉 Success!

When everything is working, you should have:

- ✅ StackWeb frontend accessible at your domain
- ✅ Supabase API responding to authentication requests
- ✅ StackEnd backend processing API calls
- ✅ All services can communicate internally
- ✅ SSL certificates automatically provisioned
- ✅ Load balancer routing traffic correctly

Your StackAI platform is now running on AWS EKS! 🚀
