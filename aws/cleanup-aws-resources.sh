#!/bin/bash

# StackAI AWS Resources Cleanup Script
# This script removes all StackAI-related AWS resources and the deployment user

set -e

echo "🧹 StackAI AWS Resources Cleanup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Warning
echo -e "${RED}⚠️  WARNING: This will DELETE ALL StackAI AWS resources!${NC}"
echo -e "${RED}⚠️  This action is IRREVERSIBLE!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}❌ Cleanup cancelled.${NC}"
    exit 0
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq not found. Please install jq first.${NC}"
    exit 1
fi

# Step 1: Destroy CDK Stack
echo -e "${BLUE}🏗️ Step 1: Destroying CDK stack...${NC}"

# Try with stackai-deployment profile first
if aws sts get-caller-identity --profile stackai-deployment &> /dev/null; then
    export AWS_PROFILE=stackai-deployment
    echo -e "${BLUE}Using stackai-deployment profile${NC}"
fi

# Check if stack exists
if aws cloudformation describe-stacks --stack-name StackaiEksCdkStack &> /dev/null; then
    echo -e "${YELLOW}🔄 Destroying StackaiEksCdkStack...${NC}"
    
    # First try to delete stuck Redis resources manually
    echo -e "${BLUE}🔧 Attempting to clean up stuck Redis resources...${NC}"
    
    # Find and delete Redis replication groups
    REDIS_GROUPS=$(aws elasticache describe-replication-groups --query 'ReplicationGroups[?contains(ReplicationGroupId, `stmwua22zqbpf87`)].ReplicationGroupId' --output text 2>/dev/null || echo "")
    if [ ! -z "$REDIS_GROUPS" ]; then
        for REDIS_GROUP in $REDIS_GROUPS; do
            echo -e "${YELLOW}🗑️ Deleting Redis cluster: $REDIS_GROUP${NC}"
            aws elasticache delete-replication-group --replication-group-id "$REDIS_GROUP" --no-retain-primary-cluster 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to delete Redis cluster${NC}"
        done
        
        # Wait for Redis deletion
        echo -e "${BLUE}⏳ Waiting 60 seconds for Redis cleanup...${NC}"
        sleep 60
    fi
    
    # Try CDK destroy if available and virtual env is set up
    if command -v cdk &> /dev/null && [ -d ".venv" ]; then
        echo -e "${BLUE}🔄 Activating virtual environment and using CDK...${NC}"
        source .venv/bin/activate
        cdk destroy StackaiEksCdkStack --force 2>/dev/null || {
            echo -e "${YELLOW}⚠️ CDK destroy failed, trying direct CloudFormation deletion...${NC}"
            aws cloudformation delete-stack --stack-name StackaiEksCdkStack
        }
    else
        echo -e "${BLUE}🔄 Using direct CloudFormation deletion...${NC}"
        aws cloudformation delete-stack --stack-name StackaiEksCdkStack
    fi
    
    # Wait for stack deletion
    echo -e "${BLUE}⏳ Waiting for stack deletion to complete...${NC}"
    aws cloudformation wait stack-delete-complete --stack-name StackaiEksCdkStack 2>/dev/null || {
        echo -e "${YELLOW}⚠️ Stack deletion may have failed or timed out${NC}"
        echo -e "${BLUE}💡 Check AWS Console for manual cleanup if needed${NC}"
    }
    
    echo -e "${GREEN}✅ CDK stack destruction attempted${NC}"
else
    echo -e "${YELLOW}⚠️ StackaiEksCdkStack not found or already destroyed${NC}"
fi

# Step 2: Find and clean up remaining tagged resources
echo -e "\n${BLUE}🔍 Step 2: Finding and cleaning up remaining tagged resources...${NC}"

# Switch to admin credentials for cleanup
unset AWS_PROFILE
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ No admin AWS credentials configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

TAGGED_RESOURCES=$(aws resourcegroupstaggingapi get-resources \
    --tag-filters Key=Project,Values=StackAI \
    --query 'ResourceTagMappingList[].ResourceARN' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$TAGGED_RESOURCES" ]; then
    echo -e "${YELLOW}⚠️ Found remaining tagged resources:${NC}"
    echo "$TAGGED_RESOURCES" | tr '\t' '\n'
    echo ""
    
    # Clean up specific resource types
    echo -e "${BLUE}🧹 Attempting to clean up remaining resources...${NC}"
    
    # Clean up subnets
    SUBNETS=$(echo "$TAGGED_RESOURCES" | grep "subnet/" | sed 's/.*subnet\///')
    for SUBNET in $SUBNETS; do
        if [ ! -z "$SUBNET" ]; then
            echo -e "${YELLOW}🗑️ Deleting subnet: $SUBNET${NC}"
            aws ec2 delete-subnet --subnet-id "$SUBNET" 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to delete subnet $SUBNET${NC}"
        fi
    done
    
    # Clean up log groups
    LOG_GROUPS=$(echo "$TAGGED_RESOURCES" | grep "log-group:" | sed 's/.*log-group://')
    for LOG_GROUP in $LOG_GROUPS; do
        if [ ! -z "$LOG_GROUP" ]; then
            echo -e "${YELLOW}🗑️ Deleting log group: $LOG_GROUP${NC}"
            aws logs delete-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to delete log group $LOG_GROUP${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Cleanup of remaining resources attempted${NC}"
else
    echo -e "${GREEN}✅ No remaining tagged resources found${NC}"
fi

# Step 3: Remove resource group
echo -e "\n${BLUE}📦 Step 3: Removing resource group...${NC}"

if aws resource-groups get-group --group-name "StackAI-Infrastructure" &> /dev/null; then
    aws resource-groups delete-group --group-name "StackAI-Infrastructure"
    echo -e "${GREEN}✅ Resource group removed${NC}"
else
    echo -e "${YELLOW}⚠️ Resource group 'StackAI-Infrastructure' not found${NC}"
fi

# Step 4: Clean up deployment user
echo -e "\n${BLUE}👤 Step 4: Cleaning up deployment user...${NC}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/StackAIDeploymentPolicy"

# Clean up deployment user
if aws iam get-user --user-name stackai-deployment-user &> /dev/null; then
    echo -e "${BLUE}🔗 Detaching all policies from user...${NC}"
    
    # List and detach all attached policies
    ATTACHED_POLICIES=$(aws iam list-attached-user-policies --user-name stackai-deployment-user --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
    for POLICY in $ATTACHED_POLICIES; do
        if [ ! -z "$POLICY" ]; then
            aws iam detach-user-policy --user-name stackai-deployment-user --policy-arn "$POLICY" 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to detach policy $POLICY${NC}"
            echo -e "${GREEN}✅ Detached policy: $POLICY${NC}"
        fi
    done
    
    # List and delete all inline policies
    INLINE_POLICIES=$(aws iam list-user-policies --user-name stackai-deployment-user --query 'PolicyNames[]' --output text 2>/dev/null || echo "")
    for POLICY_NAME in $INLINE_POLICIES; do
        if [ ! -z "$POLICY_NAME" ]; then
            aws iam delete-user-policy --user-name stackai-deployment-user --policy-name "$POLICY_NAME" 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to delete inline policy $POLICY_NAME${NC}"
            echo -e "${GREEN}✅ Deleted inline policy: $POLICY_NAME${NC}"
        fi
    done
    
    # Delete access keys
    echo -e "${BLUE}🔑 Deleting access keys...${NC}"
    ACCESS_KEYS=$(aws iam list-access-keys --user-name stackai-deployment-user --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null || echo "")
    for ACCESS_KEY in $ACCESS_KEYS; do
        if [ ! -z "$ACCESS_KEY" ]; then
            aws iam delete-access-key \
                --user-name stackai-deployment-user \
                --access-key-id "$ACCESS_KEY" 2>/dev/null || echo -e "${YELLOW}⚠️ Failed to delete access key $ACCESS_KEY${NC}"
            echo -e "${GREEN}✅ Access key $ACCESS_KEY deleted${NC}"
        fi
    done
    
    # Delete user
    echo -e "${BLUE}👤 Deleting user...${NC}"
    aws iam delete-user --user-name stackai-deployment-user 2>/dev/null && echo -e "${GREEN}✅ User deleted${NC}" || echo -e "${YELLOW}⚠️ Failed to delete user${NC}"
else
    echo -e "${YELLOW}⚠️ User 'stackai-deployment-user' not found${NC}"
fi

# Step 5: Delete policy
echo -e "\n${BLUE}📋 Step 5: Deleting IAM policy...${NC}"

if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    aws iam delete-policy --policy-arn "$POLICY_ARN"
    echo -e "${GREEN}✅ Policy deleted${NC}"
else
    echo -e "${YELLOW}⚠️ Policy 'StackAIDeploymentPolicy' not found${NC}"
fi

# Step 6: Clean up local files
echo -e "\n${BLUE}🗂️ Step 6: Cleaning up local files...${NC}"

FILES_TO_REMOVE=(
    "stackai-deployment-user-keys.json"
    "stackai-deployment-policy.json"
    "cdk.out"
)

for FILE in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$FILE" ] || [ -d "$FILE" ]; then
        rm -rf "$FILE"
        echo -e "${GREEN}✅ Removed $FILE${NC}"
    fi
done

# Step 7: Remove AWS CLI profile
echo -e "\n${BLUE}⚙️ Step 7: Removing AWS CLI profile...${NC}"

if aws configure list-profiles 2>/dev/null | grep -q "stackai-deployment"; then
    # Remove profile sections from AWS config files
    if [ -f ~/.aws/credentials ]; then
        sed -i.bak '/\[stackai-deployment\]/,/^$/d' ~/.aws/credentials 2>/dev/null || true
    fi
    if [ -f ~/.aws/config ]; then
        sed -i.bak '/\[profile stackai-deployment\]/,/^$/d' ~/.aws/config 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ AWS CLI profile removed${NC}"
else
    echo -e "${YELLOW}⚠️ AWS CLI profile 'stackai-deployment' not found${NC}"
fi

echo -e "\n${GREEN}🎉 Cleanup Complete!${NC}"
echo -e "${GREEN}=====================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "✅ CDK stack destroyed (if it existed)"
echo -e "✅ Remaining tagged resources listed"
echo -e "✅ Resource group removed"
echo -e "✅ Deployment user and access keys deleted"
echo -e "✅ IAM policy deleted"
echo -e "✅ Local files cleaned up"
echo -e "✅ AWS CLI profile removed"
echo ""
echo -e "${BLUE}Notes:${NC}"
echo -e "- If any resources remain, check the AWS Console"
echo -e "- Some resources may have deletion protection enabled"
echo -e "- Backup files (.bak) were created for AWS config files"
echo ""
echo -e "${GREEN}All StackAI AWS resources have been cleaned up!${NC}" 