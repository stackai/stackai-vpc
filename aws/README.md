# stackai_eks_cdk

This repository contains an AWS CDK (Python) project to provition a fully managed AWS EKS–based architecture.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [AWS User Setup](#aws-user-setup)
5. [Repository Structure](#repository-structure)
6. [Installation](#installation)
7. [Bootstrapping & Deployment](#bootstrapping--deployment)
8. [Project Components](#project-components)
9. [Kubernetes Manifests](#kubernetes-manifests)
10. [Environment Variables & Secrets](#environment-variables--secrets)
11. [Post-Deployment Verification](#post-deployment-verification)
12. [Further Improvements](#further-improvements)
13. [License](#license)

---

## Overview

The “stackai-onprem” monorepo originally used Docker Compose to run the following services locally:

- **MongoDB** (for Vector and other document-store needs)
- **Weaviate**
- **Supabase stack** (GoTrue, PostgREST, Realtime, Storage, pg-meta, pg-pooler, Edge Functions)
- **Unstructured API**
- **StackWeb** (Next.js frontend)
- **StackEnd** (FastAPI/Django + Celery + Redis)
- **StackRepl**

This CDK project rewrites that entire stack to run on AWS:

- **Amazon DocumentDB** (managed MongoDB) for any Mongo workloads
- **Amazon EKS** (Kubernetes) cluster to run all containerized services (Weaviate, Supabase components, Unstructured, StackWeb, StackEnd, StackRepl)
- **Amazon Aurora Serverless v2 (PostgreSQL)** for Supabase’s Postgres database
- **Amazon ElastiCache (Redis)** for StackEnd’s Celery workers and Supabase Realtime
- **Amazon S3** for Supabase Storage
- **Amazon SES** for GoTrue email sending
- **API Gateway + Lambda** for Supabase Edge Functions
- **Application Load Balancer (ALB)** via AWS Load Balancer Controller to route all HTTP(S) traffic into Kubernetes
- **Secrets Manager** to store and generate all credentials (DocumentDB admin, Aurora credentials, Supabase DB credentials, SMTP passwords, JWT secrets, etc.)
- **IAM Roles & Service Accounts (IRSA)** for pods that need AWS permissions (S3, SES, Secrets Manager)

Once deployed, the CDK app will output all key endpoints (Cluster name, DocDB endpoint, Aurora endpoint, Redis endpoint, S3 bucket name, Edge Functions URL).

---

## Features

- **Single-click deployment** of entire architecture with `cdk synth` → `cdk deploy`
- **Fully managed** backend services (DocumentDB, Aurora Serverless v2, ElastiCache, S3, SES, API Gateway)
- **EKS cluster** with managed node group across two AZs
- **Kubernetes manifests** for each service foldered under `k8s/`, applied via CDK `cluster.add_manifest(...)`
- **Ingress** driven by AWS Load Balancer Controller (ALB) with path-based routing for all endpoints
- **Secrets management** using AWS Secrets Manager and consolidated Kubernetes Secrets for environment variables
- **IAM Roles & IRSA** so pods can securely access S3, SES, Secrets Manager, etc.
- **Autoscaling hints** for Aurora and EKS (node group), with ability to extend to HPA and Cluster Autoscaler

---

## Prerequisites

1. **AWS Account & CLI**

   - An AWS account with administrative access
   - AWS CLI installed and configured
   - We'll create a dedicated deployment user with appropriate permissions (see [AWS User Setup](#aws-user-setup) below)

2. **CDK v2**

   - Install AWS CDK (v2) globally or use a recent version in a virtual environment.

   ```bash
   npm install -g aws-cdk@2.x   # or use a specific version >=2.XX

   3.	Python 3.9+
   •	Create and activate a virtual environment for Python.
   ```

python3 -m venv .venv
source .venv/bin/activate

    4.	kubectl (optional, to inspect EKS cluster after deployment)
    •	Install via package manager or curl -LO from official Kubernetes releases.

---

## AWS User Setup

For security and organization, we'll create a dedicated IAM user for deploying the StackAI infrastructure. This approach allows for:

- **Isolated permissions** specific to this deployment
- **Easy resource tracking** through consistent tagging
- **Simple cleanup** by removing all tagged resources
- **Audit trail** for deployment activities

### Option A: Automated Setup (Recommended)

We provide a script that automates the entire user creation process:

```bash
# First, configure AWS CLI with your admin credentials
aws configure

# Run the automated setup script
./setup-aws-user.sh
```

The script will:

- Create the deployment user with proper tags
- Generate and save access keys securely
- Create and attach the necessary IAM policy
- Set up the resource group for tracking
- Configure the AWS CLI profile automatically

### Option B: Manual Setup

If you prefer to create the user manually, follow these steps:

### Step 1: Create the Deployment User

First, configure your AWS CLI with administrative credentials to create the deployment user:

```bash
# Configure AWS CLI with your admin credentials (one-time setup)
aws configure
```

Create the StackAI deployment user:

```bash
# Create IAM user for StackAI deployment
aws iam create-user \
    --user-name stackai-deployment-user \
    --tags Key=Project,Value=StackAI Key=Purpose,Value=Deployment \
    --path /stackai/

# Create access key for the user
aws iam create-access-key \
    --user-name stackai-deployment-user > stackai-deployment-user-keys.json

# Display the access key (save these securely!)
cat stackai-deployment-user-keys.json
```

### Step 2: Create and Attach IAM Policy

Create a comprehensive policy for CDK deployment:

```bash
# Create IAM policy for StackAI deployment
cat > stackai-deployment-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:*",
                "iam:*",
                "ec2:*",
                "eks:*",
                "rds:*",
                "docdb:*",
                "elasticache:*",
                "s3:*",
                "secretsmanager:*",
                "apigateway:*",
                "lambda:*",
                "logs:*",
                "ses:*",
                "acm:*",
                "route53:*",
                "elasticloadbalancing:*",
                "autoscaling:*",
                "ssm:*",
                "kms:*",
                "sts:*",
                "tag:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create the policy
aws iam create-policy \
    --policy-name StackAIDeploymentPolicy \
    --policy-document file://stackai-deployment-policy.json \
    --description "Policy for StackAI CDK deployment" \
    --tags Key=Project,Value=StackAI Key=Purpose,Value=Deployment

# Attach policy to user
aws iam attach-user-policy \
    --user-name stackai-deployment-user \
    --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/StackAIDeploymentPolicy"
```

### Step 3: Create Resource Group for Easy Management

Create a resource group to track all StackAI resources:

```bash
# Create resource group for StackAI resources
aws resource-groups create-group \
    --name "StackAI-Infrastructure" \
    --description "All AWS resources for StackAI deployment" \
    --resource-query '{
        "Type": "TAG_FILTERS_1_0",
        "Query": "{\"ResourceTypeFilters\":[\"AWS::AllSupported\"],\"TagFilters\":[{\"Key\":\"Project\",\"Values\":[\"StackAI\"]}]}"
    }' \
    --tags Project=StackAI,Environment=Production,ManagedBy=CDK
```

### Step 4: Configure AWS CLI with Deployment User

Configure your AWS CLI to use the new deployment user:

```bash
# Configure AWS CLI with deployment user credentials
aws configure --profile stackai-deployment
# Enter the AccessKeyId and SecretAccessKey from stackai-deployment-user-keys.json
# Set your preferred region (e.g., us-east-1)
# Set output format to json

# Set the profile as default for this session
export AWS_PROFILE=stackai-deployment

# Verify the configuration
aws sts get-caller-identity
```

### Step 5: Resource Cleanup (When Needed)

#### Option A: Automated Cleanup (Recommended)

Use the provided cleanup script to remove everything:

```bash
# Run the automated cleanup script
./cleanup-aws-resources.sh
```

The script will automatically:

- Destroy the CDK stack
- Find and list any remaining tagged resources
- Remove the resource group
- Delete the deployment user and access keys
- Remove the IAM policy
- Clean up local credential files

#### Option B: Manual Cleanup

When you want to remove all StackAI infrastructure manually:

```bash
# First, destroy the CDK stack
cdk destroy StackaiEksCdkStack --force

# Find and delete any remaining tagged resources
aws resourcegroupstaggingapi get-resources \
    --tag-filters Key=Project,Values=StackAI \
    --query 'ResourceTagMappingList[].ResourceARN' \
    --output table

# Clean up the deployment user and policies (optional)
aws iam detach-user-policy \
    --user-name stackai-deployment-user \
    --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/StackAIDeploymentPolicy"

aws iam delete-access-key \
    --user-name stackai-deployment-user \
    --access-key-id $(cat stackai-deployment-user-keys.json | jq -r '.AccessKey.AccessKeyId')

aws iam delete-user --user-name stackai-deployment-user

aws iam delete-policy \
    --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/StackAIDeploymentPolicy"

# Remove local credential files
rm -f stackai-deployment-user-keys.json stackai-deployment-policy.json
```

---

## Repository Structure

```txt
stackai_eks_cdk/
├── bin/
│ └── stackai_eks_cdk.py # CDK entry point
├── lib/
│ └── stackai_eks_cdk_stack.py # Main CDK stack definition
├── k8s/
│ ├── supabase/
│ │ ├── goTrue_deployment.yaml
│ │ ├── postgrest_deployment.yaml
│ │ ├── realtime_deployment.yaml
│ │ ├── storage_deployment.yaml
│ │ ├── pgmeta_deployment.yaml
│ │ ├── edgefunctions_deployment.yaml
│ │ ├── configmaps_and_secrets.yaml
│ │ └── ingress_rules.yaml
│ ├── weaviate_deployment.yaml
│ ├── unstructured_deployment.yaml
│ ├── stackweb_deployment.yaml
│ ├── stackend_backend_deployment.yaml
│ ├── stackend_celery_deployment.yaml
│ ├── stackrepl_deployment.yaml
│ └── common/
│ ├── namespace.yaml
│ ├── serviceaccount_irsa.yaml # IRSA YAML for pods needing AWS permissions
│ └── rbac.yaml # RBAC for AWS Load Balancer Controller, etc.
├── requirements.txt # Python dependencies
├── cdk.json # CDK config (points to bin/stackai_eks_cdk.py)
└── README.md # This file
```

    •	bin/stackai_eks_cdk.py — Entry point that instantiates the single CDK stack.
    •	lib/stackai_eks_cdk_stack.py — Defines all AWS resources, EKS cluster, managed services, IRSA roles, and applies Kubernetes manifests.
    •	k8s/ — Contains raw Kubernetes YAML files for each service, grouped by folder. These can be used to generate or update manifests, but CDK applies them directly via cluster.add_manifest(...).
    •	requirements.txt — Lists aws-cdk-lib and constructs versions (for CDK v2 Python).

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/stackai/stackai-onprem
cd stackai-onprem/aws
```

### 2. Create and activate a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Install CDK CLI

If you haven’t installed CDK v2 globally, you can install via npm:

```bash
npm install -g aws-cdk@2.x
```

### 5. Verify CDK version

```bash
cdk --version # should be 2.x.y
```

---

## Bootstrapping & Deployment

⚠️ **Important**: Complete the [AWS User Setup](#aws-user-setup) section first to create the deployment user and configure your AWS CLI.

Before deploying any CDK v2 stacks, you must bootstrap the AWS environment once. The bootstrap step provisions an S3 bucket and IAM roles that CDK uses to store synthesized templates and assets.

### 1. Bootstrap the environment

```bash
# Make sure you're using the stackai-deployment profile
export AWS_PROFILE=stackai-deployment

# Verify your identity
aws sts get-caller-identity

# Bootstrap CDK for your account and region
cdk bootstrap
```

If you need to specify a different region:

```bash
cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/us-west-2
```

    2.	Synthesize CloudFormation templates (optional)

cdk synth

Generates the CloudFormation YAML/JSON in the cdk.out/ folder.

    3.	Deploy the stack

cdk deploy StackaiEksCdkStack --require-approval never

This will provision all AWS resources described in lib/stackai_eks_cdk_stack.py. CDK will display progress and output the following values when complete:
• EksClusterName
• DocumentDbEndpoint
• AuroraPostgresEndpoint
• RedisEndpoint
• SupabaseStorageBucketName
• EdgeFunctionsApiUrl

    4.	(Optional) Kubeconfig setup

After the EKS cluster is created, CDK will automatically update your local kubeconfig so you can interact with it via kubectl.

aws eks update-kubeconfig --name <EksClusterName> --region <REGION>
kubectl get nodes # verify that EKS nodes are ready

⸻

Project Components

1. VPC & Subnets
   • A new VPC with two AZs.
   • One public and one private subnet in each AZ.
   • A NAT Gateway in a public subnet to allow outbound traffic from private subnets.

2. Amazon DocumentDB (MongoDB)
   • A Secrets Manager secret (stackai-docdb-admin) is created with random password for docdb_admin.
   • A DocumentDB cluster in private subnets.
   • Security Group allowing EKS IP ranges (VPC CIDR) to connect on port 27017.

3. Amazon Aurora Serverless v2 (PostgreSQL)
   • A Serverless Aurora v2 cluster with an autogenerated Secrets Manager secret.
   • Runs in private subnets.
   • Security Group allowing EKS to connect on port 5432.
   • Autoscaling from 2 ACU up to 16 ACU, auto-pause after 10 minutes of inactivity.

4. Amazon ElastiCache Redis
   • A single-node Redis cluster in private subnets.
   • Security Group allowing EKS to connect on port 6379.

5. Amazon S3 Bucket (Supabase Storage)
   • Encrypted, private S3 bucket named SupabaseStorageBucket.
   • Auto-delete objects and removal policy = DESTROY (for dev/test; change in production).

6. Amazon SES Identity (GoTrue email)
   • Assumes you have already verified an SES identity (noreply@mydomain.com).
   • IAM Role / Service Account (IRSA) for GoTrue pods to call ses:SendEmail and ses:SendRawEmail.

7. IAM Roles & IRSA (Service Accounts)
   • EksAdminRole: master role for EKS cluster (optional, attaches to cluster control plane).
   • GoTrueSA: Kubernetes ServiceAccount in supabase namespace allowing SES access.
   • StorageSA: ServiceAccount in supabase namespace with s3:PutObject, s3:GetObject, etc., on the Supabase bucket.
   • SupabaseDbSecret: Secret in Secrets Manager with username/password for Supabase containers (pg-pooler, PostgREST, Realtime, Storage, pg-meta).
   • CelerySA: ServiceAccount in stackend namespace (no AWS API calls needed if Redis/RDS are accessed by hostname).
   • Additional IRSA manifests may be added in k8s/common/serviceaccount_irsa.yaml for other pod permissions.

8. Amazon EKS Cluster
   • Created across two AZs.
   • Kubernetes version v1.24.
   • Managed Node Group with t3.large instances (2 to 4 nodes).
   • Endpoint access set to public & private.
   • Add-on: AWS Load Balancer Controller and IAM role for it (RBAC and permissions defined in k8s/common/rbac.yaml).

9. Kubernetes Namespaces & RBAC
   • Namespaces: supabase, weaviate, unstructured, stackweb, stackend, stackrepl.
   • A ConfigMap in kube-system for ALB Ingress (cluster name and ingress class).
   • Additional RBAC manifests for AWS Load Balancer Controller in k8s/common/rbac.yaml.

10. Kubernetes Manifests

Each service has its own Deployment, Service, and Ingress (where applicable). They live under k8s/ and are applied via CDK:
• supabase/
• configmaps_and_secrets.yaml (defines supabase-env-secret containing all .env-style values for GoTrue, PostgREST, Realtime, Storage, pg-meta, pg-pooler).
• goTrue_deployment.yaml, postgrest_deployment.yaml, etc. (each Deployment + Service).
• ingress_rules.yaml (Ingress resource with path-based routing in supabase namespace).
• weaviate_deployment.yaml (Deployment, Service, Ingress).
• unstructured_deployment.yaml (Deployment, Service, Ingress).
• stackweb_deployment.yaml (Deployment, Service, Ingress).
• stackend_backend_deployment.yaml (Deployment, Service, Ingress).
• stackend_celery_deployment.yaml (Deployment only; Celery workers do not expose services).
• stackrepl_deployment.yaml (Deployment, Service).
• common/
• namespace.yaml (defines all namespaces).
• serviceaccount_irsa.yaml (IRSA ServiceAccount bindings, if additional pods need AWS permissions).
• rbac.yaml (ClusterRole, ClusterRoleBinding for AWS Load Balancer Controller, etc.).

11. API Gateway & Lambda (Supabase Edge Functions)
    • Creates a single Lambda function (EdgeFunctionLambda) with inline “Hello world” code.
    • Creates an API Gateway REST API named StackAiEdgeFunctionsApi.
    • Defines a proxy resource /functions/{proxy+} that forwards all requests to the Lambda.

⸻

Kubernetes Manifests

All raw YAML manifests are checked in under the k8s/ directory. CDK uses cluster.add_manifest(...) (inline JSON/YAML) to apply them directly. If you wish to modify or regenerate manifests, edit the YAML files and update the CDK stack accordingly.

Key files:
• k8s/common/namespace.yaml
• k8s/common/serviceaccount_irsa.yaml
• k8s/common/rbac.yaml
• k8s/supabase/configmaps_and_secrets.yaml
• k8s/supabase/goTrue_deployment.yaml
• k8s/supabase/postgrest_deployment.yaml
• k8s/supabase/realtime_deployment.yaml
• k8s/supabase/storage_deployment.yaml
• k8s/supabase/pgmeta_deployment.yaml
• k8s/supabase/edgefunctions_deployment.yaml
• k8s/supabase/ingress_rules.yaml
• k8s/weaviate_deployment.yaml
• k8s/unstructured_deployment.yaml
• k8s/stackweb_deployment.yaml
• k8s/stackend_backend_deployment.yaml
• k8s/stackend_celery_deployment.yaml
• k8s/stackrepl_deployment.yaml

⸻

Environment Variables & Secrets

All environment variables required by Supabase components (GoTrue, PostgREST, Realtime, Storage, pg-meta, pg-pooler) are consolidated into a single Kubernetes Secret called supabase-env-secret in the supabase namespace. Example keys include:
• PGMETA_DB_PASSWORD → pulled from the Aurora Serverless v2 secret
• GOTRUE_JWT_SECRET, POSTGREST_JWT_SECRET → random JWT secrets you must replace before deployment
• GOTRUE_SMTP_PASSWORD → SES SMTP password (store in Secrets Manager or directly in supabase-env-secret if using a test account)
• SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY → your own generated Supabase keys

Rather than hardcoding secrets in manifests, CDK references rds_secret.secret_value_from_json("password") for the Aurora password. DocumentDB admin credentials are stored in stackai-docdb-admin (Secrets Manager) and injected into pods that need MongoDB access via IRSA or environment variables if applicable.

If you need to add more variables, edit stackai_eks_cdk_stack.py under the SupabaseConfigAndSecrets manifest, and update the corresponding YAML in k8s/supabase/configmaps_and_secrets.yaml.

⸻

Post-Deployment Verification 1. Check CDK Outputs
After cdk deploy, note the following outputs:
• EksClusterName → Name of the EKS cluster
• DocumentDbEndpoint → Endpoint for DocumentDB (MongoDB)
• AuroraPostgresEndpoint → Host:port for Aurora Serverless v2 Postgres
• RedisEndpoint → Redis host
• SupabaseStorageBucketName → S3 bucket name
• EdgeFunctionsApiUrl → URL for Supabase Edge Functions API 2. Verify EKS Cluster

aws eks update-kubeconfig --name <EksClusterName> --region <REGION>
kubectl get nodes
kubectl get namespaces
kubectl get deployments,services,ingress -A

    3.	Test Service Endpoints

After AWS Load Balancer Controller provisions an ALB, you’ll have a hostname (findable in the AWS Console under EC2 → Load Balancers, look for an ALB with the name beginning with “a2w…”). Replace <ALB_HOSTNAME> in the commands below:

# Supabase GoTrue health

curl http://<ALB_HOSTNAME>/auth/health

# Supabase PostgREST

curl http://<ALB_HOSTNAME>/rest/v1/

# Supabase GraphQL (if enabled)

curl http://<ALB_HOSTNAME>/graphql/v1/

# Supabase Realtime

curl http://<ALB_HOSTNAME>/realtime/health

# Supabase Storage

curl http://<ALB_HOSTNAME>/storage/v1/buckets

# Supabase pg-meta

curl http://<ALB_HOSTNAME>/pg/health

# StackWeb UI

curl http://<ALB_HOSTNAME>/

# StackEnd (backend) health

curl http://<ALB_HOSTNAME>/stackend/health

# Unstructured API

curl http://<ALB_HOSTNAME>/unstructured/

# Supabase Edge Functions

curl <EdgeFunctionsApiUrl>/functions/hello

# Weaviate (if domain set up)

curl http://weaviate.yourdomain.com/

# Unstructured (if domain set up)

curl http://unstructured.yourdomain.com/unstructured/

# StackWeb (if domain set up)

curl http://app.yourdomain.com/

# StackEnd (if domain set up)

curl http://backend.yourdomain.com/stackend/health

⸻

Further Improvements
• HTTPS / TLS
• Request or import an ACM certificate, and update Ingress annotations to reference the certificate’s ARN
• Example:

alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/abcd-efgh-ijkl-...
alb.ingress.kubernetes.io/ssl-redirect: "443"

    •	Kubernetes Secrets Store CSI Driver
    •	Instead of storing sensitive values in Kubernetes secret.stringData, use the Secrets Store CSI driver to fetch AWS Secrets Manager or Parameter Store values at runtime.
    •	Autoscaling
    •	Add Horizontal Pod Autoscalers (HPA) for high-traffic services (e.g., Supabase Realtime, StackEnd backend).
    •	Configure the EKS Cluster Autoscaler to scale EC2 instances based on pod demands.
    •	Fine-tune Aurora auto-scaling configurations (min/max ACU).
    •	Monitoring & Logging
    •	Enable CloudWatch Container Insights for EKS.
    •	Deploy Prometheus & Grafana in the cluster for detailed metrics.
    •	Configure CloudWatch Alarms for critical metrics (e.g., high CPU/Memory on pods, RDS CPU utilization, Redis memory).
    •	CI/CD Pipelines
    •	Integrate with GitHub Actions, CodePipeline, or other CI/CD tools to automate cdk synth and cdk deploy.
    •	Implement canary or blue/green deployments for Kubernetes workloads (e.g., via Argo Rollouts, Flagger).
    •	Production Hardening
    •	Adjust removal policies (e.g., set to RETAIN instead of DESTROY).
    •	Enable encryption at rest for Aurora, DocumentDB, ElastiCache, and S3.
    •	Configure multi-AZ replication for production-level resilience.

⸻

License

This project is licensed under the MIT License. See the LICENSE file for details.
