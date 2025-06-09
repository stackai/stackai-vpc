#!/bin/bash

# Build and Push StackAI Docker Images
# This script builds Docker images from the source code and pushes them to a registry

set -e

# Configuration - UPDATE THESE VALUES
ECR_REGISTRY="881490119564.dkr.ecr.us-east-2.amazonaws.com"
REGION="us-east-2"
PROJECT_ROOT="/Users/alfonso.hernandez/Documents/StackAI/stackai-onprem"

echo "🐳 Building and pushing StackAI Docker images..."

# 1. Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# 2. Create ECR repositories if they don't exist
echo "📦 Creating ECR repositories..."
for repo in stackai/stackweb stackai/stackend stackai/stackrepl; do
    aws ecr describe-repositories --repository-names $repo --region $REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $repo --region $REGION
done

# 3. Build StackWeb image
echo "🌐 Building StackWeb image..."
cd $PROJECT_ROOT/stackweb

# Create Dockerfile for StackWeb if it doesn't exist
if [ ! -f Dockerfile ]; then
cat > Dockerfile <<EOF
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT 3000
CMD ["node", "server.js"]
EOF
fi

docker build -t $ECR_REGISTRY/stackai/stackweb:latest .
docker push $ECR_REGISTRY/stackai/stackweb:latest

# 4. Build StackEnd image  
echo "⚙️ Building StackEnd image..."
cd $PROJECT_ROOT/stackend

# Create Dockerfile for StackEnd if it doesn't exist
if [ ! -f Dockerfile ]; then
cat > Dockerfile <<EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash stackend
RUN chown -R stackend:stackend /app
USER stackend

# Expose port
EXPOSE 8000

# Default command (can be overridden for Celery)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi

docker build -t $ECR_REGISTRY/stackai/stackend:latest .
docker push $ECR_REGISTRY/stackai/stackend:latest

# 5. Build StackRepl image
echo "💻 Building StackRepl image..."
cd $PROJECT_ROOT/stackrepl

# Create Dockerfile for StackRepl if it doesn't exist
if [ ! -f Dockerfile ]; then
cat > Dockerfile <<EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including code execution tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    nodejs \
    npm \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash stackrepl
RUN chown -R stackrepl:stackrepl /app
USER stackrepl

# Default command
CMD ["python", "main.py"]
EOF
fi

docker build -t $ECR_REGISTRY/stackai/stackrepl:latest .
docker push $ECR_REGISTRY/stackai/stackrepl:latest

echo "✅ All images built and pushed successfully!"
echo ""
echo "📋 Built images:"
echo "- $ECR_REGISTRY/stackai/stackweb:latest"
echo "- $ECR_REGISTRY/stackai/stackend:latest" 
echo "- $ECR_REGISTRY/stackai/stackrepl:latest"
echo ""
echo "🔄 Update the deploy-applications.sh script with these image URIs" 