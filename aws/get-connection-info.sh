#!/bin/bash

# Get Connection Information from CDK Deployment
# This script extracts database endpoints, cluster info, and other connection details

set -e

REGION="us-east-2"
STACK_NAME="StackaiEksCdkStack"

echo "📋 Getting connection information from CDK deployment..."

# 1. Get CloudFormation stack outputs
echo "🔍 Retrieving CloudFormation outputs..."
OUTPUTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs' --output json)

echo "📄 CDK Stack Outputs:"
echo $OUTPUTS | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"'

# 2. Get EKS cluster info
echo ""
echo "🏗️ EKS Cluster Information:"
CLUSTER_NAME=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="EksClusterName") | .OutputValue')
echo "Cluster Name: $CLUSTER_NAME"

if [ "$CLUSTER_NAME" != "null" ]; then
    aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.{Status:status,Endpoint:endpoint,Version:version}' --output table
fi

# 3. Get RDS/Aurora endpoint
echo ""
echo "🗄️ Aurora Database Information:"
AURORA_ENDPOINT=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="AuroraPostgresEndpoint") | .OutputValue')
echo "Aurora Endpoint: $AURORA_ENDPOINT"

# 4. Get DocumentDB endpoint
echo ""
echo "📊 DocumentDB Information:"
DOCDB_ENDPOINT=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="DocumentDbEndpoint") | .OutputValue')
echo "DocumentDB Endpoint: $DOCDB_ENDPOINT"

# 5. Get Redis endpoint
echo ""
echo "🔥 Redis Information:"
REDIS_ENDPOINT=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="RedisEndpoint") | .OutputValue')
echo "Redis Endpoint: $REDIS_ENDPOINT"

# 6. Get S3 bucket
echo ""
echo "🪣 S3 Storage Information:"
S3_BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="SupabaseStorageBucketName") | .OutputValue')
echo "S3 Bucket: $S3_BUCKET"

# 7. Generate connection strings for deployment
echo ""
echo "🔗 Connection Strings for Deployment:"
echo "=================================="

if [ "$AURORA_ENDPOINT" != "null" ]; then
    echo "DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@$AURORA_ENDPOINT:5432/postgres"
fi

if [ "$REDIS_ENDPOINT" != "null" ]; then
    echo "REDIS_URL=redis://$REDIS_ENDPOINT:6379/0"
fi

if [ "$DOCDB_ENDPOINT" != "null" ]; then
    echo "MONGODB_URL=mongodb://docdb_admin:YOUR_PASSWORD@$DOCDB_ENDPOINT:27017/?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
fi

echo ""
echo "🔧 Next Steps:"
echo "1. Update deploy-applications.sh with these connection strings"
echo "2. Get actual passwords from AWS Secrets Manager"
echo "3. Run build-images.sh to build Docker images"
echo "4. Run deploy-applications.sh to deploy applications"

# 8. Get kubectl config command
echo ""
echo "⚙️ Configure kubectl:"
if [ "$CLUSTER_NAME" != "null" ]; then
    echo "aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME"
fi 