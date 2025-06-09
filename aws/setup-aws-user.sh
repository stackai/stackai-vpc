#!/bin/bash

# StackAI AWS User Setup Script
# This script creates a dedicated IAM user for StackAI deployment with proper permissions and resource grouping

set -e

echo "🚀 StackAI AWS User Setup"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️ jq not found. Installing via package manager...${NC}"
    # Try to install jq based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install jq
        else
            echo -e "${RED}❌ Please install jq manually: brew install jq${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y jq
    else
        echo -e "${RED}❌ Please install jq manually${NC}"
        exit 1
    fi
fi

# Verify AWS credentials are configured
echo -e "${BLUE}🔍 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ No AWS credentials configured. Please run 'aws configure' first with admin credentials.${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: ${ACCOUNT_ID}${NC}"

# Step 1: Create the deployment user
echo -e "\n${BLUE}📝 Step 1: Creating StackAI deployment user...${NC}"

if aws iam get-user --user-name stackai-deployment-user &> /dev/null; then
    echo -e "${YELLOW}⚠️ User 'stackai-deployment-user' already exists. Skipping creation.${NC}"
else
    aws iam create-user \
        --user-name stackai-deployment-user \
        --tags Key=Project,Value=StackAI Key=Purpose,Value=Deployment \
        --path /stackai/
    echo -e "${GREEN}✅ User created successfully${NC}"
fi

# Step 2: Create access key
echo -e "\n${BLUE}🔑 Step 2: Creating access key...${NC}"

# Check if access key already exists
ACCESS_KEYS=$(aws iam list-access-keys --user-name stackai-deployment-user --query 'AccessKeyMetadata[].AccessKeyId' --output text)
if [ ! -z "$ACCESS_KEYS" ]; then
    echo -e "${YELLOW}⚠️ Access key already exists for user. Using existing key.${NC}"
    echo -e "${YELLOW}💡 If you need a new key, delete the existing one first:${NC}"
    echo -e "${YELLOW}   aws iam delete-access-key --user-name stackai-deployment-user --access-key-id $ACCESS_KEYS${NC}"
else
    aws iam create-access-key \
        --user-name stackai-deployment-user > stackai-deployment-user-keys.json
    echo -e "${GREEN}✅ Access key created and saved to stackai-deployment-user-keys.json${NC}"
    echo -e "${YELLOW}🔐 Please save these credentials securely:${NC}"
    cat stackai-deployment-user-keys.json | jq .
fi

# Step 3: Create IAM policy
echo -e "\n${BLUE}📋 Step 3: Creating IAM policy...${NC}"

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

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/StackAIDeploymentPolicy"

if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Policy 'StackAIDeploymentPolicy' already exists. Skipping creation.${NC}"
else
    aws iam create-policy \
        --policy-name StackAIDeploymentPolicy \
        --policy-document file://stackai-deployment-policy.json \
        --description "Policy for StackAI CDK deployment" \
        --tags Key=Project,Value=StackAI Key=Purpose,Value=Deployment
    echo -e "${GREEN}✅ Policy created successfully${NC}"
fi

# Step 4: Attach policy to user
echo -e "\n${BLUE}🔗 Step 4: Attaching policy to user...${NC}"

aws iam attach-user-policy \
    --user-name stackai-deployment-user \
    --policy-arn "$POLICY_ARN"
echo -e "${GREEN}✅ Policy attached successfully${NC}"

# Step 5: Create resource group
echo -e "\n${BLUE}📦 Step 5: Creating resource group...${NC}"

if aws resource-groups get-group --group-name "StackAI-Infrastructure" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Resource group 'StackAI-Infrastructure' already exists. Skipping creation.${NC}"
else
    aws resource-groups create-group \
        --name "StackAI-Infrastructure" \
        --description "All AWS resources for StackAI deployment" \
        --resource-query '{
            "Type": "TAG_FILTERS_1_0",
            "Query": "{\"ResourceTypeFilters\":[\"AWS::AllSupported\"],\"TagFilters\":[{\"Key\":\"Project\",\"Values\":[\"StackAI\"]}]}"
        }' \
        --tags Project=StackAI,Environment=Production,ManagedBy=CDK
    echo -e "${GREEN}✅ Resource group created successfully${NC}"
fi

# Step 6: Configure AWS CLI profile
echo -e "\n${BLUE}⚙️ Step 6: Configuring AWS CLI profile...${NC}"

if [ -f "stackai-deployment-user-keys.json" ]; then
    ACCESS_KEY_ID=$(cat stackai-deployment-user-keys.json | jq -r '.AccessKey.AccessKeyId')
    SECRET_ACCESS_KEY=$(cat stackai-deployment-user-keys.json | jq -r '.AccessKey.SecretAccessKey')
    
    # Get current region
    CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
    
    # Configure the profile
    aws configure set aws_access_key_id "$ACCESS_KEY_ID" --profile stackai-deployment
    aws configure set aws_secret_access_key "$SECRET_ACCESS_KEY" --profile stackai-deployment
    aws configure set region "$CURRENT_REGION" --profile stackai-deployment
    aws configure set output json --profile stackai-deployment
    
    echo -e "${GREEN}✅ AWS CLI profile 'stackai-deployment' configured${NC}"
    
    # Test the configuration
    echo -e "\n${BLUE}🧪 Testing the new configuration...${NC}"
    AWS_PROFILE=stackai-deployment aws sts get-caller-identity
    echo -e "${GREEN}✅ Configuration test successful${NC}"
    
else
    echo -e "${YELLOW}⚠️ Access key file not found. Please configure manually:${NC}"
    echo -e "${YELLOW}   aws configure --profile stackai-deployment${NC}"
fi

echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "${GREEN}==================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Export the profile: ${YELLOW}export AWS_PROFILE=stackai-deployment${NC}"
echo -e "2. Bootstrap CDK: ${YELLOW}cdk bootstrap${NC}"
echo -e "3. Deploy the stack: ${YELLOW}cdk deploy StackaiEksCdkStack${NC}"
echo ""
echo -e "${BLUE}Files created:${NC}"
echo -e "- stackai-deployment-user-keys.json (${RED}keep secure!${NC})"
echo -e "- stackai-deployment-policy.json"
echo ""
echo -e "${BLUE}To use this setup:${NC}"
echo -e "${YELLOW}export AWS_PROFILE=stackai-deployment${NC}"
echo -e "${YELLOW}aws sts get-caller-identity${NC}"
echo ""
echo -e "${BLUE}To clean up everything later:${NC}"
echo -e "${YELLOW}./cleanup-aws-resources.sh${NC}" 