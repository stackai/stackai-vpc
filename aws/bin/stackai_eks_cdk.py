#!/usr/bin/env python3
"""
StackAI EKS CDK Application Entry Point

This application creates a complete AWS infrastructure stack to replace 
the Docker Compose "stackai-onprem" setup with a fully managed AWS EKS-based architecture.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import from lib
sys.path.append(str(Path(__file__).parent.parent))

import aws_cdk as cdk
from lib.stackai_eks_cdk_stack import StackaiEksCdkStack

# Get environment variables for stack configuration
account = os.environ.get('CDK_DEFAULT_ACCOUNT', cdk.Aws.ACCOUNT_ID)
region = os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')

app = cdk.App()

# Create the main stack
StackaiEksCdkStack(
    app, 
    "StackaiEksCdkStack",
    description="StackAI on AWS EKS - Complete infrastructure for running StackAI on managed AWS services",
    env=cdk.Environment(
        account=account,
        region=region
    ),
    # Add tags to all resources for better management
    tags={
        "Project": "StackAI",
        "Environment": "Production",
        "ManagedBy": "CDK",
        "Owner": "StackAI-Team"
    }
)

app.synth() 