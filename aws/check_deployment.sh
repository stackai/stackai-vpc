#!/bin/bash

# Check deployment progress script
echo "=== StackAI EKS Deployment Progress Check ==="
echo "Time: $(date)"
echo

# Check if CDK process is running
echo "1. Checking CDK deployment process..."
CDK_PID=$(ps aux | grep "cdk deploy" | grep -v grep | awk '{print $2}')
if [ -n "$CDK_PID" ]; then
    echo "✅ CDK deployment is running (PID: $CDK_PID)"
else
    echo "❌ No CDK deployment process found"
fi
echo

# Check CloudFormation stack status
echo "2. Checking CloudFormation stack status..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name StackaiEksCdkStack --region us-east-1 --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "📋 Stack Status: $STACK_STATUS"
else
    echo "❓ Stack not found or not accessible"
fi
echo

# Check recent CloudFormation events
echo "3. Recent CloudFormation events (last 5)..."
aws cloudformation describe-stack-events \
    --stack-name StackaiEksCdkStack \
    --region us-east-1 \
    --query 'StackEvents[0:5].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
    --output table 2>/dev/null || echo "❓ Could not retrieve stack events"
echo

# Check EKS cluster if it exists
echo "4. Checking EKS cluster..."
CLUSTER_STATUS=$(aws eks describe-cluster --name StackAiEksCluster --region us-east-1 --query 'cluster.status' --output text 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "🎯 EKS Cluster Status: $CLUSTER_STATUS"
else
    echo "❓ EKS cluster not found or not accessible yet"
fi
echo

echo "=== Check complete ==="
echo "💡 Tip: Run this script again in a few minutes to see progress" 